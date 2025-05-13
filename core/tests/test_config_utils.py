from django.test import TestCase, TransactionTestCase
from django.db import connection
from django.core.cache import cache
import json
import unittest

from core.utils.config_utils import (
    ConfigManager, get_config, get_bool_config, get_int_config,
    get_float_config, get_str_config, get_list_config, get_dict_config,
    clear_config_cache
)


# 使用TransactionTestCase而不是TestCase
# 避免自动数据库迁移的依赖
class ConfigManagerTest(TransactionTestCase):
    """测试配置管理器功能"""
    
    # 禁用自动事务，直接使用原始连接
    serialized_rollback = False
    
    def setUp(self):
        """测试前准备"""
        # 清除所有相关的缓存
        cache.clear()
        
        try:
            # 检查表是否存在
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM {ConfigManager.CONFIG_TABLE} LIMIT 1")
        except Exception:
            # 如果表不存在，则创建测试表
            with connection.cursor() as cursor:
                # 使用简化的表结构
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {ConfigManager.CONFIG_TABLE} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        description TEXT
                    )
                """)
        
        # 直接在数据库中插入一些测试配置
        with connection.cursor() as cursor:
            # 插入测试数据
            # 布尔类型配置
            cursor.execute(
                f"INSERT OR REPLACE INTO {ConfigManager.CONFIG_TABLE} (key, value, description) VALUES (?, ?, ?)",
                ["test_bool", json.dumps(True), "测试布尔值配置"]
            )
            
            # 整数类型配置
            cursor.execute(
                f"INSERT OR REPLACE INTO {ConfigManager.CONFIG_TABLE} (key, value, description) VALUES (?, ?, ?)",
                ["test_int", json.dumps(123), "测试整数配置"]
            )
            
            # 浮点数类型配置
            cursor.execute(
                f"INSERT OR REPLACE INTO {ConfigManager.CONFIG_TABLE} (key, value, description) VALUES (?, ?, ?)",
                ["test_float", json.dumps(3.14), "测试浮点数配置"]
            )
            
            # 字符串类型配置
            cursor.execute(
                f"INSERT OR REPLACE INTO {ConfigManager.CONFIG_TABLE} (key, value, description) VALUES (?, ?, ?)",
                ["test_str", json.dumps("hello world"), "测试字符串配置"]
            )
            
            # 列表类型配置
            cursor.execute(
                f"INSERT OR REPLACE INTO {ConfigManager.CONFIG_TABLE} (key, value, description) VALUES (?, ?, ?)",
                ["test_list", json.dumps([1, 2, 3]), "测试列表配置"]
            )
            
            # 字典类型配置
            cursor.execute(
                f"INSERT OR REPLACE INTO {ConfigManager.CONFIG_TABLE} (key, value, description) VALUES (?, ?, ?)",
                ["test_dict", json.dumps({"name": "测试", "value": 100}), "测试字典配置"]
            )
            
            # 类型不匹配的配置
            cursor.execute(
                f"INSERT OR REPLACE INTO {ConfigManager.CONFIG_TABLE} (key, value, description) VALUES (?, ?, ?)",
                ["test_wrong_type", json.dumps("not a number"), "测试类型不匹配"]
            )
            
            # SMTP配置示例
            smtp_config = {
                "enable_smtp": True,
                "smtp_server": "smtp.example.com",
                "smtp_port": 465,
                "security_type": "ssl",
                "require_authentication": True,
                "smtp_username": "test@example.com",
                "smtp_password": "password123",
                "sender_email": "noreply@example.com",
                "sender_name": "测试系统",
                "send_timeout": 30
            }
            cursor.execute(
                f"INSERT OR REPLACE INTO {ConfigManager.CONFIG_TABLE} (key, value, description) VALUES (?, ?, ?)",
                ["email_settings", json.dumps(smtp_config), "邮件服务设置"]
            )
    
    def tearDown(self):
        """测试后清理"""
        # 清除测试数据
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {ConfigManager.CONFIG_TABLE} WHERE key LIKE 'test_%'")
            cursor.execute(f"DELETE FROM {ConfigManager.CONFIG_TABLE} WHERE key = 'email_settings'")
        
        # 清除缓存
        cache.clear()
    
    def test_get_config(self):
        """测试获取配置的基本功能"""
        # 测试获取存在的配置
        value = get_config("test_str")
        self.assertEqual(value, "hello world")
        
        # 测试获取不存在的配置，应返回默认值
        value = get_config("non_existent_key", default="default value")
        self.assertEqual(value, "default value")
        
        # 测试获取空键，应返回默认值
        value = get_config("", default="default for empty key")
        self.assertEqual(value, "default for empty key")
    
    def test_typed_config(self):
        """测试获取指定类型的配置"""
        # 测试布尔值
        value = get_bool_config("test_bool")
        self.assertTrue(value)
        self.assertIsInstance(value, bool)
        
        # 测试整数
        value = get_int_config("test_int")
        self.assertEqual(value, 123)
        self.assertIsInstance(value, int)
        
        # 测试浮点数
        value = get_float_config("test_float")
        self.assertEqual(value, 3.14)
        self.assertIsInstance(value, float)
        
        # 测试字符串
        value = get_str_config("test_str")
        self.assertEqual(value, "hello world")
        self.assertIsInstance(value, str)
        
        # 测试列表
        value = get_list_config("test_list")
        self.assertEqual(value, [1, 2, 3])
        self.assertIsInstance(value, list)
        
        # 测试字典
        value = get_dict_config("test_dict")
        self.assertEqual(value, {"name": "测试", "value": 100})
        self.assertIsInstance(value, dict)
    
    def test_wrong_type(self):
        """测试类型不匹配的情况"""
        # 请求整数，但实际是字符串，应返回默认值
        value = get_int_config("test_wrong_type", default=999)
        self.assertEqual(value, 999)
    
    def test_caching(self):
        """测试缓存功能"""
        # 首次获取，应从数据库读取
        value1 = get_str_config("test_str")
        self.assertEqual(value1, "hello world")
        
        # 修改数据库中的值，但不清除缓存
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {ConfigManager.CONFIG_TABLE} SET value = ? WHERE key = ?",
                [json.dumps("modified value"), "test_str"]
            )
        
        # 再次获取，应从缓存读取旧值
        value2 = get_str_config("test_str")
        self.assertEqual(value2, "hello world")  # 仍然是旧值
        
        # 清除缓存
        clear_config_cache("test_str")
        
        # 再次获取，应从数据库读取新值
        value3 = get_str_config("test_str")
        self.assertEqual(value3, "modified value")  # 现在是新值
        
        # 测试禁用缓存
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {ConfigManager.CONFIG_TABLE} SET value = ? WHERE key = ?",
                [json.dumps("no cache value"), "test_str"]
            )
        
        # 使用use_cache=False参数
        value4 = get_str_config("test_str", use_cache=False)
        self.assertEqual(value4, "no cache value")  # 直接从数据库读取了新值
    
    def test_email_settings(self):
        """测试获取电子邮件设置"""
        # 获取电子邮件配置
        email_config = get_dict_config("email_settings")
        
        # 验证配置内容
        self.assertTrue(email_config["enable_smtp"])
        self.assertEqual(email_config["smtp_server"], "smtp.example.com")
        self.assertEqual(email_config["smtp_port"], 465)
        self.assertEqual(email_config["security_type"], "ssl")
        self.assertTrue(email_config["require_authentication"])
        self.assertEqual(email_config["smtp_username"], "test@example.com")
        self.assertEqual(email_config["smtp_password"], "password123")
        self.assertEqual(email_config["sender_email"], "noreply@example.com")
        self.assertEqual(email_config["sender_name"], "测试系统")
        self.assertEqual(email_config["send_timeout"], 30)
    
    def test_clear_all_cache(self):
        """测试清除所有缓存"""
        # 先获取几个配置，让它们进入缓存
        get_bool_config("test_bool")
        get_int_config("test_int")
        get_str_config("test_str")
        
        # 修改所有测试配置
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {ConfigManager.CONFIG_TABLE} SET value = ? WHERE key = 'test_bool'",
                [json.dumps(False)]
            )
            cursor.execute(
                f"UPDATE {ConfigManager.CONFIG_TABLE} SET value = ? WHERE key = 'test_int'",
                [json.dumps(456)]
            )
            cursor.execute(
                f"UPDATE {ConfigManager.CONFIG_TABLE} SET value = ? WHERE key = 'test_str'",
                [json.dumps("all cleared")]
            )
        
        # 清除所有缓存
        clear_config_cache()
        
        # 验证所有配置都是从数据库获取的新值
        self.assertFalse(get_bool_config("test_bool"))
        self.assertEqual(get_int_config("test_int"), 456)
        self.assertEqual(get_str_config("test_str"), "all cleared")


# 也提供一个跳过数据库测试的单元测试，只测试基本功能
class ConfigManagerUnitTest(unittest.TestCase):
    """配置管理器的单元测试，不需要数据库"""
    
    def test_type_conversion(self):
        """测试类型转换功能"""
        # 模拟一个配置字典
        config = {"test": 123}
        
        # 测试类型检查
        self.assertTrue(isinstance(config["test"], int))
        
        # 测试类型转换 - 这里主要是演示，实际没有调用ConfigManager
        int_val = int(config["test"])
        self.assertEqual(int_val, 123)
        
        str_val = str(config["test"])
        self.assertEqual(str_val, "123")
        
        # 测试JSON序列化/反序列化
        json_str = json.dumps(config)
        decoded = json.loads(json_str)
        self.assertEqual(decoded["test"], 123) 