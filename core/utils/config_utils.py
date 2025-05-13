from django.db import connection
from django.core.cache import cache
import json
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    通用配置管理器
    从数据库中读取配置信息，支持缓存和默认值
    该类不依赖于admin_panel或games模块，可以作为独立的核心功能使用
    """
    
    # 缓存过期时间(秒)
    CACHE_TIMEOUT = 3600  # 1小时
    
    # 配置表名
    CONFIG_TABLE = 'admin_panel_configsettings'
    
    @classmethod
    def get_config(cls, key, default=None, use_cache=True):
        """
        获取指定键的配置
        
        参数:
            key (str): 配置键名
            default (any, optional): 如果配置不存在时返回的默认值
            use_cache (bool, optional): 是否使用缓存
            
        返回:
            配置值或默认值(如果配置不存在)
        """
        if not key:
            logger.warning("无效的配置键")
            return default
        
        # 缓存键名
        cache_key = f"config_settings:{key}"
        
        # 如果启用缓存，尝试从缓存获取
        if use_cache:
            cached_config = cache.get(cache_key)
            if cached_config is not None:
                logger.debug(f"从缓存中获取配置: {key}")
                return cached_config
        
        try:
            # 从数据库查询配置
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT value FROM {cls.CONFIG_TABLE} WHERE key = %s",
                    [key]
                )
                row = cursor.fetchone()
                
                if row:
                    # 解析JSON数据
                    try:
                        config_value = json.loads(row[0])
                        # 存入缓存
                        if use_cache:
                            cache.set(cache_key, config_value, cls.CACHE_TIMEOUT)
                        logger.debug(f"从数据库获取配置: {key}")
                        return config_value
                    except json.JSONDecodeError:
                        logger.error(f"配置值不是有效的JSON: {key}")
                        return default
                
                logger.debug(f"配置不存在，使用默认值: {key}")
                return default
                
        except Exception as e:
            logger.exception(f"获取配置时出错: {key}, {str(e)}")
            return default
    
    @classmethod
    def get_typed_config(cls, key, config_type, default=None, use_cache=True):
        """
        获取指定类型的配置，如果类型不匹配返回默认值
        
        参数:
            key (str): 配置键名
            config_type (type): 期望的配置类型
            default (any, optional): 默认值
            use_cache (bool, optional): 是否使用缓存
            
        返回:
            指定类型的配置值或默认值
        """
        value = cls.get_config(key, default, use_cache)
        
        # 检查类型是否匹配
        if value is not None and not isinstance(value, config_type):
            logger.warning(f"配置类型不匹配: {key}, 期望 {config_type.__name__}, 实际 {type(value).__name__}")
            return default
            
        return value
    
    @classmethod
    def get_bool_config(cls, key, default=False, use_cache=True):
        """获取布尔类型配置"""
        return cls.get_typed_config(key, bool, default, use_cache)
    
    @classmethod
    def get_int_config(cls, key, default=0, use_cache=True):
        """获取整数类型配置"""
        return cls.get_typed_config(key, int, default, use_cache)
    
    @classmethod
    def get_float_config(cls, key, default=0.0, use_cache=True):
        """获取浮点类型配置"""
        return cls.get_typed_config(key, float, default, use_cache)
    
    @classmethod
    def get_str_config(cls, key, default="", use_cache=True):
        """获取字符串类型配置"""
        return cls.get_typed_config(key, str, default, use_cache)
    
    @classmethod
    def get_list_config(cls, key, default=None, use_cache=True):
        """获取列表类型配置"""
        if default is None:
            default = []
        return cls.get_typed_config(key, list, default, use_cache)
    
    @classmethod
    def get_dict_config(cls, key, default=None, use_cache=True):
        """获取字典类型配置"""
        if default is None:
            default = {}
        return cls.get_typed_config(key, dict, default, use_cache)
    
    @classmethod
    def clear_cache(cls, key=None):
        """
        清除配置缓存
        
        参数:
            key (str, optional): 要清除的配置键，如果为None则清除所有配置缓存
        """
        if key:
            cache_key = f"config_settings:{key}"
            cache.delete(cache_key)
            logger.debug(f"已清除配置缓存: {key}")
        else:
            # 清除所有配置缓存
            # 注意: 这会清除所有以'config_settings:'开头的缓存键
            # 如果需要更精细的控制，可以使用缓存的模式删除功能
            keys = cache.keys('config_settings:*')
            if keys:
                cache.delete_many(keys)
            logger.debug("已清除所有配置缓存")


# 创建导出的便捷函数
get_config = ConfigManager.get_config
get_bool_config = ConfigManager.get_bool_config
get_int_config = ConfigManager.get_int_config
get_float_config = ConfigManager.get_float_config
get_str_config = ConfigManager.get_str_config
get_list_config = ConfigManager.get_list_config
get_dict_config = ConfigManager.get_dict_config
clear_config_cache = ConfigManager.clear_cache 