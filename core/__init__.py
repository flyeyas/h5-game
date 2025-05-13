"""Core模块
提供系统核心功能，包括共享数据模型和通用工具

此模块包含:
- 共享数据模型 (models)
- 用户模型 (user_models)
- 通用工具函数
- 配置管理工具 (utils.config_utils)
"""

# 版本信息
__version__ = "1.0.0"

# 定义要导出的符号
__all__ = ['__version__']

# 添加配置管理功能
try:
    from .utils.config_utils import (
        ConfigManager, 
        get_config, 
        get_bool_config, 
        get_int_config, 
        get_float_config,
        get_str_config, 
        get_list_config, 
        get_dict_config,
        clear_config_cache
    )
    
    # 添加到导出符号列表
    __all__.extend([
        'ConfigManager', 
        'get_config',
        'get_bool_config', 
        'get_int_config', 
        'get_float_config',
        'get_str_config', 
        'get_list_config', 
        'get_dict_config',
        'clear_config_cache'
    ])
except ImportError:
    # 如果导入失败，不添加这些功能
    pass

# 添加邮件相关功能
try:
    from .mail import send_mail, send_verification_code, test_smtp_connection
    from .email_config import EmailConfig
    from .email_utils import email_settings_context, get_smtp_connection
    
    __all__.extend([
        'send_mail', 'send_verification_code', 'test_smtp_connection',
        'EmailConfig', 'email_settings_context', 'get_smtp_connection'
    ])
except ImportError:
    # 如果导入失败，不添加这些功能
    pass

# 兼容旧版API的get_config函数
def _legacy_get_config(module_name, config_name=None):
    """获取配置的便捷函数（兼容旧版API）
    
    从数据库获取配置
    """
    # 延迟导入，避免循环依赖
    from admin_panel.models import ConfigSettings
    
    # 如果只提供了module_name而没有提供config_name，
    # 我们假设module_name就是配置键
    key = module_name
    return ConfigSettings.get_config(key)

# 导出兼容旧版API的函数
get_email_config = lambda: _legacy_get_config('email_settings')

__all__ = [
    # ... 保持现有导出列表 ...
]
