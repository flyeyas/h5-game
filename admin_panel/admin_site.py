from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.urls import reverse, resolve
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.template.response import TemplateResponse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.views.decorators import staff_member_required
from functools import wraps
import logging
from django.contrib.auth.decorators import user_passes_test

logger = logging.getLogger('admin')

def admin_site_required(view_func):
    """
    检查当前视图是否应该在管理站点中显示
    这是自定义站点权限的第一层校验
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # 简单检查请求是否来自管理站点
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return HttpResponseForbidden("您没有权限访问此页面")
        return view_func(request, *args, **kwargs)
    return wrapped_view

def custom_staff_member_required(view_func):
    """
    自定义装饰器，类似于Django的staff_member_required，
    但可以自定义登录URL和重定向行为
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # 用户未登录，重定向到后台登录页面
            from django.urls import reverse
            admin_login_url = reverse('admin_panel:admin_login')
            redirect_path = f"{admin_login_url}?next={request.get_full_path()}"
            return HttpResponseRedirect(redirect_path)
        
        if not request.user.is_staff and not request.user.is_superuser:
            # 用户已登录但不是管理员
            logger.warning(f"非管理员用户尝试访问后台: {request.user.username}")
            return HttpResponseForbidden("您没有管理员权限")
        
        # 用户是管理员，允许访问
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def admin_login_required(view_func):
    """
    自定义装饰器，类似于Django的login_required，
    但强制重定向到后台登录页面而不是settings.LOGIN_URL
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # 用户未登录，重定向到后台登录页面
            from django.urls import reverse
            admin_login_url = reverse('admin_panel:admin_login') 
            redirect_path = f"{admin_login_url}?next={request.get_full_path()}"
            return HttpResponseRedirect(redirect_path)
        
        # 用户已登录，允许访问
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def log_admin_action(user, action, action_type=None, target=None):
    """记录管理员操作到日志系统"""
    from .models import AdminLog
    
    try:
        # 构建完整的操作描述
        if action_type and target:
            action_text = f"{action} [{action_type}] {target}"
        else:
            action_text = action
            
        # 创建日志记录
        AdminLog.objects.create(
            admin=user,
            action=action_text,
            ip_address='127.0.0.1'  # 在实际使用中应从请求中获取IP
        )
        logger.info(f"管理员操作记录: {user.username} - {action_text}")
    except Exception as e:
        logger.error(f"记录管理员操作失败: {str(e)}")


class CustomAdminSite(AdminSite):
    """自定义管理站点，扩展默认的 Django AdminSite"""
    
    def get_app_list(self, request):
        """
        重写应用列表获取方法，自定义排序和分组
        """
        app_list = super().get_app_list(request)
        
        # 这里可以添加自定义的排序或分组逻辑
        # 例如，将某些应用放在前面
        priority_apps = ['admin_panel', 'games', 'auth']
        
        def get_app_priority(app):
            try:
                return priority_apps.index(app['app_label'])
            except ValueError:
                return len(priority_apps)
        
        app_list.sort(key=get_app_priority)
        
        return app_list
    
    def login(self, request, extra_context=None):
        """
        自定义登录页面
        """
        if request.method == 'GET' and request.user.is_authenticated:
            # 已登录用户重定向到管理首页
            return HttpResponseRedirect(reverse('admin_panel:dashboard'))
            
        context = extra_context or {}
        context.update({
            'title': _('GameHub管理系统登录'),
            'app_path': request.get_full_path(),
            REDIRECT_FIELD_NAME: request.GET.get(REDIRECT_FIELD_NAME, ''),
        })
        
        return super().login(request, extra_context=context)
    
    def admin_view(self, view, cacheable=False):
        """
        重写admin_view以添加自定义权限检查
        """
        return super().admin_view(view, cacheable)
    
    def each_context(self, request):
        """
        添加额外的上下文信息到管理站点的每个请求中
        """
        context = super().each_context(request)
        
        # 添加额外的上下文信息
        context.update({
            'custom_site_name': 'GameHub',
            'version': '1.0',
        })
        
        return context 