"""
自定义django-allauth适配器
用于自定义登录、注册和社交账号集成行为
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.conf import settings
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import json
import traceback

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """自定义账号适配器，用于修改默认的allauth行为"""
    
    def get_login_redirect_url(self, request):
        """
        登录成功后的重定向URL
        优先使用next参数，其次使用settings中的配置
        """
        next_url = request.GET.get('next')
        if next_url:
            return next_url
        return settings.LOGIN_REDIRECT_URL

    def get_logout_redirect_url(self, request):
        """登出后的重定向URL"""
        return '/'
    
    def get_email_verification_redirect_url(self, email_address):
        """邮箱验证后的重定向URL"""
        return reverse('games:login')
    
    def is_open_for_signup(self, request):
        """是否开放注册功能"""
        # 可以根据实际需求修改，例如：只允许邀请注册
        return True
    
    def render_template(self, template_name, request, context):
        """
        自定义模板渲染过程
        添加额外的上下文变量
        """
        context['allauth_enabled'] = True
        return super().render_template(template_name, request, context)
    
    def get_login_context(self, request, **kwargs):
        """
        登录视图的上下文
        添加标识login_form的变量用于模板判断
        """
        context = super().get_login_context(request, **kwargs)
        context['login_form'] = context.get('form')
        return context
    
    def get_signup_context(self, request, **kwargs):
        """
        注册视图的上下文
        """
        context = super().get_signup_context(request, **kwargs)
        return context


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """自定义社交账号适配器，用于修改默认的社交登录行为"""
    
    def get_connect_redirect_url(self, request, socialaccount):
        """连接社交账号后的重定向URL"""
        return reverse('games:profile_settings')
    
    def is_open_for_signup(self, request, sociallogin):
        """检查社交登录用户是否可以自动创建账号"""
        # 这里可以添加逻辑来控制是否允许特定社交平台的用户注册
        return True
    
    def populate_user(self, request, sociallogin, data):
        """
        根据社交账号数据填充用户资料
        在创建用户前被调用，可以修改用户数据
        """
        user = super().populate_user(request, sociallogin, data)
        
        # 根据社交账号提供商自定义用户信息
        if sociallogin.account.provider == 'google':
            # 从Google获取用户信息
            data = sociallogin.account.extra_data
            
            # 如果用户名为空，尝试使用Google提供的名称作为用户名
            if not user.username and 'name' in data:
                # 可能需要处理用户名唯一性
                from django.contrib.auth.models import User
                base_username = data.get('name').lower().replace(' ', '_')
                username = base_username
                
                # 确保用户名唯一
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                user.username = username
        
        return user
    
    def pre_social_login(self, request, sociallogin):
        """社交登录前处理"""
        # 可以在此处添加额外的登录前处理逻辑
        try:
            logger.debug(f"社交登录前置处理: 提供商={sociallogin.account.provider}, 用户={getattr(sociallogin.user, 'username', 'unknown')}")
            
            # 记录额外信息，用于调试
            extra_data = getattr(sociallogin.account, 'extra_data', {})
            if extra_data:
                logger.debug(f"社交账户数据: {json.dumps(extra_data, ensure_ascii=False)[:200]}...")
                
        except Exception as e:
            logger.error(f"社交登录前置处理异常: {e}")
        
        return super().pre_social_login(request, sociallogin)
    
    def configure_oauth_client(self, client):
        """配置OAuth客户端"""
        # 设置重试策略
        retry_strategy = Retry(
            total=5,  # 最多重试5次
            backoff_factor=1.0,  # 重试间隔因子
            status_forcelist=[429, 500, 502, 503, 504],  # 哪些HTTP状态码需要重试
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]  # 允许重试的HTTP方法
        )
        
        # 设置会话
        try:
            # 使用标准HTTP适配器，不使用代理
            adapter = HTTPAdapter(max_retries=retry_strategy)
            client.session.mount("https://", adapter)
            client.session.mount("http://", adapter)
            logger.info("配置OAuth客户端使用直接连接")
            
            # 设置是否验证SSL证书
            verify_ssl = True
            if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS'):
                providers = settings.SOCIALACCOUNT_PROVIDERS
                if 'google' in providers and 'REQUESTS_PARAMS' in providers['google']:
                    req_params = providers['google']['REQUESTS_PARAMS']
                    if 'verify' in req_params:
                        verify_ssl = req_params['verify']
            
            client.session.verify = verify_ssl
            
            # 设置超时
            timeout = 60  # 默认超时时间60秒
            if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS'):
                providers = settings.SOCIALACCOUNT_PROVIDERS
                if 'google' in providers and 'REQUESTS_TIMEOUT' in providers['google']:
                    timeout = providers['google']['REQUESTS_TIMEOUT']
            
            client.session.timeout = timeout
            logger.info(f"OAuth客户端超时设置: {timeout}秒")
            
            # 设置用户代理以避免被某些服务器拒绝
            client.session.headers.update({
                'User-Agent': 'GameHub/1.0 (Compatible; Python/Requests)'
            })
            
            # 添加调试信息
            logger.debug(f"OAuth客户端配置完成: session={client.session}, headers={client.session.headers}")
        except Exception as e:
            logger.error(f"配置OAuth客户端时出错: {e}")
            logger.error(traceback.format_exc())
            # 确保不会因为配置错误而中断流程
        
        return client
    
    def get_app(self, request, provider, client_id=None):
        """
        获取社交应用配置
        
        参数:
            request: 请求对象
            provider: 提供商名称
            client_id: 客户端ID (可选)
        
        返回:
            SocialApp: 社交应用对象
        """
        app = super().get_app(request, provider, client_id=client_id)
        return app
    
    def process_callback_error(self, request, provider, error):
        """
        处理OAuth回调错误
        这个方法在allauth中被用来处理OAuth回调过程中的错误
        """
        logger.error(f"OAuth回调错误: 提供商={provider}, 错误={error}")
        # 记录详细追踪信息用于调试
        logger.error(f"错误详情: {traceback.format_exc()}")
        
        # 记录请求信息
        try:
            logger.debug(f"请求路径: {request.path}")
            logger.debug(f"请求GET参数: {dict(request.GET.items())}")
            logger.debug(f"已认证用户: {request.user.is_authenticated}")
        except Exception as e:
            logger.error(f"记录请求信息时出错: {e}")
        
        # 调用父类方法
        result = super().process_callback_error(request, provider, error)
        return result
    
    def save_user(self, request, sociallogin, form=None):
        """保存用户后处理"""
        try:
            logger.info(f"保存社交登录用户: {sociallogin.user.username}")
        except Exception as e:
            logger.error(f"保存用户日志记录失败: {e}")
        
        return super().save_user(request, sociallogin, form) 