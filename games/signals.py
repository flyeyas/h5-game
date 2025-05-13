"""
信号处理模块，处理用户注册、登录等事件
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
import logging
from django.contrib.auth.models import User
from .models import FrontUser, UserProfile

# 获取日志记录器
logger = logging.getLogger(__name__)

@receiver(post_save, sender=FrontUser)
def user_created(sender, instance, created, **kwargs):
    """
    处理用户创建事件
    """
    if created:
        # 新用户创建时的逻辑
        logger.info(f"新用户创建: user_id={instance.id}, username={instance.username}")
        
        # 记录首次密码设置时间
        instance.last_password_change = timezone.now()
        instance.save(update_fields=['last_password_change'])

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    处理用户登录事件
    """
    # 仅处理前台用户
    if isinstance(user, FrontUser):
        # 记录登录尝试
        user.record_login_attempt(success=True)
        
        # 记录登录日志
        logger.info(f"用户登录成功: user_id={user.id}, username={user.username}, ip={get_client_ip(request)}")

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    处理用户退出登录事件
    """
    # 仅处理前台用户
    if user and isinstance(user, FrontUser):
        # 记录退出登录日志
        logger.info(f"用户退出登录: user_id={user.id}, username={user.username}, ip={get_client_ip(request)}")

@receiver(pre_save, sender=FrontUser)
def password_change_handler(sender, instance, **kwargs):
    """
    处理密码修改事件
    """
    # 尝试获取旧实例
    try:
        old_instance = FrontUser.objects.get(pk=instance.pk)
        
        # 检查密码是否发生变化
        if old_instance.password != instance.password:
            # 记录密码修改时间
            instance.last_password_change = timezone.now()
            
            # 记录密码修改日志
            logger.info(f"用户密码修改: user_id={instance.id}, username={instance.username}")
    except FrontUser.DoesNotExist:
        # 新用户创建，不需要处理
        pass

def get_client_ip(request):
    """
    获取客户端IP地址
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """当创建新用户时，自动创建用户资料"""
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"为用户 {instance.username} 创建了新的资料")
        except Exception as e:
            logger.error(f"创建用户资料时出错: {str(e)}") 