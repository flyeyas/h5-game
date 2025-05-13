#!/usr/bin/env python
"""
配置管理工具演示脚本
展示如何使用core.utils.config_utils模块读取和管理配置
"""
import os
import sys
import json
import django

# 添加项目根目录到Python路径（向上两级）
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

# 导入配置管理工具
from core.utils.config_utils import (
    get_config, get_bool_config, get_int_config, get_float_config,
    get_str_config, get_list_config, get_dict_config, clear_config_cache
)

def display_config(key, value):
    """打印配置信息"""
    value_type = type(value).__name__
    print(f"配置 '{key}' (类型: {value_type}): {value}")

def main():
    """主函数"""
    print("配置管理工具演示")
    print("=" * 50)
    
    # 1. 获取电子邮件配置
    print("\n1. 获取电子邮件配置")
    email_config = get_dict_config("email_settings")
    if email_config:
        print("找到电子邮件配置:")
        for key, value in email_config.items():
            print(f"  {key}: {value}")
    else:
        print("未找到电子邮件配置，返回默认值: {}")
    
    # 2. 使用不同类型的getter函数
    print("\n2. 使用不同类型的getter函数")
    
    # 布尔值配置
    enable_smtp = get_bool_config("email_settings.enable_smtp", default=False)
    display_config("email_settings.enable_smtp", enable_smtp)
    
    # 整数配置
    smtp_port = get_int_config("email_settings.smtp_port", default=25)
    display_config("email_settings.smtp_port", smtp_port)
    
    # 字符串配置
    smtp_server = get_str_config("email_settings.smtp_server", default="localhost")
    display_config("email_settings.smtp_server", smtp_server)
    
    # 3. 获取不存在的配置，使用默认值
    print("\n3. 获取不存在的配置，使用默认值")
    non_existent = get_config("non_existent_key", default="默认值")
    display_config("non_existent_key", non_existent)
    
    # 4. 缓存管理
    print("\n4. 缓存管理")
    print("首次获取配置 'email_settings' (从数据库)")
    email_config = get_dict_config("email_settings")
    
    print("再次获取同一配置 (从缓存)")
    email_config_cached = get_dict_config("email_settings")
    
    if id(email_config) == id(email_config_cached):
        print("警告: 对象ID相同，这可能表明Python对相同字典对象进行了引用")
    else:
        print("对象ID不同，但内容应该相同")
    
    print("清除 'email_settings' 的缓存")
    clear_config_cache("email_settings")
    
    print("再次获取配置 (从数据库)")
    email_config_fresh = get_dict_config("email_settings")
    
    # 5. 获取完整配置
    print("\n5. 获取特定配置")
    # 特定类型的配置例子
    system_settings = get_dict_config("system_settings", default={
        "maintenance_mode": False,
        "debug_enabled": True,
        "cache_timeout": 3600,
        "max_login_attempts": 5
    })
    print("系统设置:")
    for key, value in system_settings.items():
        print(f"  {key}: {value}")
    
    # 6. 配置类型错误处理
    print("\n6. 配置类型错误处理")
    # 尝试获取一个应该是整数的配置，但可能是字符串
    try:
        wrong_type = get_int_config("email_settings.smtp_server", default=0)
        display_config("email_settings.smtp_server (尝试作为整数)", wrong_type)
    except Exception as e:
        print(f"捕获到异常: {e}")
    
    print("\n演示完成")

if __name__ == "__main__":
    main() 