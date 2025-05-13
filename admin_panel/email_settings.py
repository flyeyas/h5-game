from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
import logging

# 导入配置设置模型
from admin_panel.models import ConfigSettings

# 获取日志记录器
logger = logging.getLogger(__name__)

class EmailSettings:
    """
    处理邮件设置的单例类。
    设置将从数据库中获取
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
            cls._instance = super(EmailSettings, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance
    
    def _load_settings(self):
        """
        加载邮件设置
        从数据库加载配置
        """
        # 尝试从数据库获取配置
        config = ConfigSettings.get_config(self._config_key)
        
        if config:
            # 从数据库获取成功
            logger.debug("从数据库加载邮件设置成功")
            self._update_from_dict(config)
            return
        
        # 如果数据库中不存在，使用默认值
        logger.info("数据库中不存在邮件配置，使用默认值")
        
        # 将默认值保存到数据库
        try:
            # 使用默认值创建配置字典
            default_config = {
                'enable_smtp': self.enable_smtp,
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'security_type': self.security_type,
                'require_authentication': self.require_authentication,
                'smtp_username': self.smtp_username,
                'smtp_password': self.smtp_password,
                'sender_email': self.sender_email,
                'sender_name': self.sender_name,
                'send_timeout': self.send_timeout
            }
            
            # 保存到数据库
            ConfigSettings.set_config(
                self._config_key, 
                default_config, 
                "邮件服务器默认配置"
            )
            logger.info("已将默认邮件设置保存到数据库")
        except Exception as e:
            logger.error(f"将默认邮件设置保存到数据库失败: {str(e)}")
    
    def _update_from_dict(self, settings_dict):
        """从字典更新设置值"""
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def save(self):
        """
        保存设置到数据库
        """
        # 创建设置字典
        settings_dict = {
            'enable_smtp': self.enable_smtp,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'security_type': self.security_type,
            'require_authentication': self.require_authentication,
            'smtp_username': self.smtp_username,
            'smtp_password': self.smtp_password,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'send_timeout': self.send_timeout
        }
        
        # 保存到数据库
        try:
            success = ConfigSettings.set_config(
                self._config_key, 
                settings_dict, 
                "邮件服务器配置"
            )
            if success:
                # 更新缓存
                cache.set('email_settings', settings_dict, 3600)  # 缓存1小时
                logger.info("邮件设置已成功保存到数据库")
                return True
            else:
                logger.error("保存邮件设置到数据库失败")
                return False
        except Exception as e:
            logger.error(f"保存邮件设置到数据库时发生错误: {str(e)}")
            return False
    
    @classmethod
    def get_settings(cls):
        """获取邮件设置的单例实例"""
        return cls()
    
    @classmethod
    def clear_cache(cls):
        """清除邮件设置缓存"""
        cache.delete('email_settings')
        # 同时清除ConfigSettings的缓存
        ConfigSettings.clear_cache(cls._config_key) 