import contextlib
from django.conf import settings
from django.core.mail import get_connection
import logging

from .email_config import EmailConfig

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def email_settings_context():
    """
    一个上下文管理器，用于临时替换Django的EMAIL_*设置，使用数据库中的配置。
    用法:
        with email_settings_context():
            send_mail(...) # 将使用数据库中的配置
    """
    # 获取当前设置
    old_email_backend = getattr(settings, 'EMAIL_BACKEND', None)
    old_email_host = getattr(settings, 'EMAIL_HOST', None)
    old_email_port = getattr(settings, 'EMAIL_PORT', None)
    old_email_host_user = getattr(settings, 'EMAIL_HOST_USER', None)
    old_email_host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
    old_email_use_tls = getattr(settings, 'EMAIL_USE_TLS', None)
    old_email_use_ssl = getattr(settings, 'EMAIL_USE_SSL', None)
    old_default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    
    # 获取数据库配置
    email_config = EmailConfig.get_settings()
    
    # 只在开启SMTP时才应用配置
    if email_config.enable_smtp:
        # 临时应用新设置
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = email_config.smtp_server
        settings.EMAIL_PORT = email_config.smtp_port
        settings.EMAIL_USE_TLS = email_config.security_type == 'tls'
        settings.EMAIL_USE_SSL = email_config.security_type == 'ssl'
        
        if email_config.require_authentication:
            settings.EMAIL_HOST_USER = email_config.smtp_username
            settings.EMAIL_HOST_PASSWORD = email_config.smtp_password
        else:
            settings.EMAIL_HOST_USER = ''
            settings.EMAIL_HOST_PASSWORD = ''
            
        # 设置发件人地址
        if email_config.sender_name:
            settings.DEFAULT_FROM_EMAIL = f"{email_config.sender_name} <{email_config.sender_email}>"
        else:
            settings.DEFAULT_FROM_EMAIL = email_config.sender_email
        
        try:
            # 提供上下文
            yield
        finally:
            # 恢复原设置
            if old_email_backend is not None:
                settings.EMAIL_BACKEND = old_email_backend
            if old_email_host is not None:
                settings.EMAIL_HOST = old_email_host
            if old_email_port is not None:
                settings.EMAIL_PORT = old_email_port
            if old_email_host_user is not None:
                settings.EMAIL_HOST_USER = old_email_host_user
            if old_email_host_password is not None:
                settings.EMAIL_HOST_PASSWORD = old_email_host_password
            if old_email_use_tls is not None:
                settings.EMAIL_USE_TLS = old_email_use_tls
            if old_email_use_ssl is not None:
                settings.EMAIL_USE_SSL = old_email_use_ssl
            if old_default_from_email is not None:
                settings.DEFAULT_FROM_EMAIL = old_default_from_email
    else:
        # 如果SMTP没有启用，直接提供上下文而不修改设置
        yield


def get_smtp_connection():
    """
    获取已配置的SMTP连接对象。
    用于需要多次发送电子邮件的批处理任务，以避免重复建立连接。
    
    返回:
        连接对象或None（如果SMTP未配置）
    """
    email_config = EmailConfig.get_settings()
    
    if not email_config.enable_smtp:
        logger.warning("尝试获取SMTP连接，但SMTP服务未启用")
        return None
    
    connection_params = {
        'host': email_config.smtp_server,
        'port': email_config.smtp_port,
        'use_tls': email_config.security_type == 'tls',
        'use_ssl': email_config.security_type == 'ssl',
        'timeout': email_config.send_timeout,
    }
    
    if email_config.require_authentication:
        connection_params['username'] = email_config.smtp_username
        connection_params['password'] = email_config.smtp_password
    
    try:
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            **connection_params
        )
        return connection
    except Exception as e:
        logger.exception(f"获取SMTP连接时出错: {str(e)}")
        return None 