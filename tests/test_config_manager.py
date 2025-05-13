import os
import sys
import unittest
import re
from unittest.mock import patch, MagicMock

# 配置Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
import django
django.setup()

from django.core.cache import cache

# 导入要测试的模块
from admin_panel.models import ConfigSettings
import core

# 这个测试文件已经过时，因为config_manager已经被移除
# 我们将修改测试用例以使用ConfigSettings模型

class ConfigSettingsTestCase(unittest.TestCase):
    """ConfigSettings测试用例类"""
    
    def setUp(self):
        """测试前准备工作"""
        # 清除缓存
        cache.clear()
        
    def tearDown(self):
        """测试后清理工作"""
        # 清除缓存
        cache.clear()
        
        # 删除测试数据
        ConfigSettings.objects.filter(key__startswith='test_').delete()
    
    def test_get_config(self):
        """测试获取配置"""
        # 创建测试配置
        test_config = {"key1": "value1", "key2": 123}
        ConfigSettings.set_config('test_settings', test_config, '测试配置')
        
        # 调用测试方法
        result = ConfigSettings.get_config('test_settings')
        
        # 验证结果
        self.assertEqual(result, test_config)
    
    def test_get_config_with_default(self):
        """测试获取不存在的配置，返回默认值"""
        # 调用测试方法
        default_value = {"default": True}
        result = ConfigSettings.get_config('non_existent_key', default_value)
        
        # 验证结果
        self.assertEqual(result, default_value)
    
    def test_set_config(self):
        """测试设置配置"""
        # 测试数据
        test_key = 'test_set_config'
        test_value = {"a": 1, "b": 2}
        test_desc = '测试配置'
        
        # 调用测试方法
        config_obj = ConfigSettings.set_config(test_key, test_value, test_desc)
        
        # 验证结果
        self.assertEqual(config_obj.key, test_key)
        self.assertEqual(config_obj.value, test_value)
        self.assertEqual(config_obj.description, test_desc)
        
        # 验证缓存已更新
        cached_value = cache.get(f"config_settings:{test_key}")
        self.assertEqual(cached_value, test_value)
    
    def test_update_existing_config(self):
        """测试更新已存在的配置"""
        # 创建初始配置
        test_key = 'test_update_config'
        initial_value = {"a": 1, "b": 2}
        ConfigSettings.set_config(test_key, initial_value, '初始配置')
        
        # 更新配置
        updated_value = {"a": 3, "b": 4, "c": 5}
        config_obj = ConfigSettings.set_config(test_key, updated_value, '已更新配置')
        
        # 验证结果
        self.assertEqual(config_obj.value, updated_value)
        self.assertEqual(config_obj.description, '已更新配置')
        
        # 验证从数据库获取的值也已更新
        db_config = ConfigSettings.objects.get(key=test_key)
        self.assertEqual(db_config.value, updated_value)
    
    def test_delete_config(self):
        """测试删除配置"""
        # 创建测试配置
        test_key = 'test_delete_config'
        test_value = {"to_be_deleted": True}
        ConfigSettings.set_config(test_key, test_value)
        
        # 调用测试方法
        ConfigSettings.delete_config(test_key)
        
        # 验证结果
        with self.assertRaises(ConfigSettings.DoesNotExist):
            ConfigSettings.objects.get(key=test_key)
        
        # 验证缓存已清除
        self.assertIsNone(cache.get(f"config_settings:{test_key}"))
    
    def test_clear_cache(self):
        """测试清除缓存"""
        # 创建测试配置并确保其在缓存中
        test_key = 'test_clear_cache'
        test_value = {"cached": True}
        ConfigSettings.set_config(test_key, test_value)
        
        # 验证缓存存在
        self.assertEqual(cache.get(f"config_settings:{test_key}"), test_value)
        
        # 调用测试方法
        ConfigSettings.clear_cache(test_key)
        
        # 验证缓存已清除
        self.assertIsNone(cache.get(f"config_settings:{test_key}"))
        
        # 但数据库中的记录仍然存在
        db_config = ConfigSettings.objects.get(key=test_key)
        self.assertEqual(db_config.value, test_value)


class CoreUtilsTestCase(unittest.TestCase):
    """Core工具类测试用例"""
    
    def setUp(self):
        """测试前准备工作"""
        # 清除缓存
        cache.clear()
        
    def tearDown(self):
        """测试后清理工作"""
        # 清除缓存
        cache.clear()
    
    def test_get_email_config(self):
        """测试get_email_config函数"""
        # 创建patch
        with patch('admin_panel.models.ConfigSettings.get_config') as mock_get_config:
            # 设置mock返回值
            email_config = {
                "smtp_server": "smtp.example.com",
                "port": 587,
                "username": "test@example.com",
                "password": "password123",
                "use_tls": True
            }
            mock_get_config.return_value = email_config
            
            # 调用测试方法
            result = core.get_email_config()
            
            # 验证结果
            mock_get_config.assert_called_once_with('email_settings')
            self.assertEqual(result, email_config)
    
    def test_core_get_config(self):
        """测试core.get_config方法"""
        # 创建patch
        with patch('admin_panel.models.ConfigSettings.get_config') as mock_get_config:
            # 设置mock返回值
            mock_get_config.return_value = {"key1": "value1"}
            
            # 调用测试方法
            result = core.get_config('test_settings')
            
            # 验证结果
            mock_get_config.assert_called_once_with('test_settings')
            self.assertEqual(result, {"key1": "value1"})


if __name__ == '__main__':
    unittest.main() 