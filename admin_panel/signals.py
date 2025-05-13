"""
管理后台信号处理模块
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import logging

from .admin_user import AdminUser

# 获取日志记录器
logger = logging.getLogger(__name__)

@receiver(post_save, sender=AdminUser)
def admin_user_post_save(sender, instance, created, **kwargs):
    """
    管理员用户保存后的处理
    
    参数:
        sender: 发送信号的模型类
        instance: 保存的实例
        created: 是否是新创建的实例
    """
    if created:
        logger.info(f"新管理员创建: user_id={instance.id}, username={instance.username}")
    else:
        logger.info(f"管理员信息更新: user_id={instance.id}, username={instance.username}")

@receiver(pre_delete, sender=AdminUser)
def admin_user_pre_delete(sender, instance, **kwargs):
    """
    管理员用户删除前的处理
    
    参数:
        sender: 发送信号的模型类
        instance: 要删除的实例
    """
    logger.warning(f"删除管理员: user_id={instance.id}, username={instance.username}")

@receiver(pre_delete, sender=User)
def prevent_admin_user_deletion(sender, instance, **kwargs):
    """
    阻止ID为1的超级管理员用户被删除
    """
    if instance.id == 1:
        logger.warning(f"尝试删除系统超级管理员（ID=1）被阻止")
        error_message = "系统超级管理员账号不允许被删除！"
        # 记录尝试删除系统管理员用户的操作
        logger.warning(f"用户尝试删除系统超级管理员: {instance.username}")
        # 抛出权限错误异常
        raise PermissionDenied(error_message) 