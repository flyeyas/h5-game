from django.db import models
from django.conf import settings
from django.core.cache import cache
import logging
import json

logger = logging.getLogger(__name__)

class EmailConfig:
    """
    处理邮件配置的单例类，用于从数据库读取SMTP配置信息。
    该类不依赖于admin_panel或games模块，可以作为独立的核心功能使用。
    """
    # 单例实例
    _instance = None
    
    # 数据库配置键
    _config_key = 'email_settings'
    
    # 设置默认值
    enable_smtp = False
    smtp_server = ""
    smtp_port = 25
    security_type = "none"  # none, ssl, tls
    require_authentication = False
    smtp_username = ""
    smtp_password = ""
    sender_email = ""
    sender_name = ""
    send_timeout = 30
    
    def __new__(cls):
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super(EmailConfig, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance
    
    def _load_settings(self):
        """
        加载邮件设置
        从数据库加载配置
        """
        # 首先尝试从缓存获取
        cache_key = f"config_settings:{self._config_key}"
        config = cache.get(cache_key)
        
        if config:
            # 从缓存获取成功
            logger.debug("从缓存加载邮件设置成功")
            self._update_from_dict(config)
            return
        
        try:
            # 如果缓存中没有，尝试从ConfigSettings表获取
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT value FROM admin_panel_configsettings WHERE key = %s",
                    [self._config_key]
                )
                row = cursor.fetchone()
                
                if row:
                    # 解析JSON数据
                    config = json.loads(row[0])
                    # 存入缓存
                    cache.set(cache_key, config, 3600)  # 缓存1小时
                    logger.debug("从数据库加载邮件设置成功")
                    self._update_from_dict(config)
                    return
                
            # 如果数据库中不存在，使用默认值
            logger.info("数据库中不存在邮件配置，使用默认值")
        except Exception as e:
            logger.error(f"从数据库加载邮件设置失败: {str(e)}")
    
    def _update_from_dict(self, settings_dict):
        """从字典更新设置值"""
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def get_settings(cls):
        """获取邮件设置的单例实例"""
        return cls()
    
    @classmethod
    def clear_cache(cls):
        """清除邮件设置缓存"""
        cache_key = f"config_settings:{cls._config_key}"
        cache.delete(cache_key)
    
    def get_django_email_settings(self):
        """
        返回Django邮件设置字典，
        可以用于动态配置Django的邮件发送功能
        """
        if not self.enable_smtp:
            return None
        
        # 准备Django邮件配置字典
        email_settings = {
            'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_HOST': self.smtp_server,
            'EMAIL_PORT': self.smtp_port,
            'EMAIL_USE_TLS': self.security_type == 'tls',
            'EMAIL_USE_SSL': self.security_type == 'ssl',
            'DEFAULT_FROM_EMAIL': f"{self.sender_name} <{self.sender_email}>" if self.sender_name else self.sender_email,
        }
        
        # 如果需要认证，添加账号信息
        if self.require_authentication:
            email_settings['EMAIL_HOST_USER'] = self.smtp_username
            email_settings['EMAIL_HOST_PASSWORD'] = self.smtp_password
        
        return email_settings 