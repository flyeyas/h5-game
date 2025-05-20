from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.conf import settings
from django.core.cache import cache
from django.utils import translation

from .models_menu_settings import Language, WebsiteSetting


class LanguageModelTest(TestCase):
    """测试Language模型功能"""
    
    def setUp(self):
        # 清除缓存
        cache.clear()
        
        # 清除所有已存在的Language实例
        Language.objects.all().delete()
        
        # 创建测试语言
        self.en_language = Language.objects.create(
            code='en',
            name='English',
            is_active=True,
            is_default=True
        )
        self.zh_language = Language.objects.create(
            code='zh',
            name='中文',
            is_active=True,
            is_default=False
        )
    
    def test_default_language_setting(self):
        """测试默认语言设置"""
        # 验证英语是默认语言
        self.assertTrue(self.en_language.is_default)
        self.assertFalse(self.zh_language.is_default)
        
        # 将中文设为默认语言
        self.zh_language.is_default = True
        self.zh_language.save()
        
        # 重新获取英语语言对象（应该已不是默认）
        self.en_language.refresh_from_db()
        
        # 验证中文已成为默认语言，且英语不再是默认语言
        self.assertFalse(self.en_language.is_default)
        self.assertTrue(self.zh_language.is_default)


class LanguageManagementViewTest(TestCase):
    """测试语言管理视图功能"""
    
    def setUp(self):
        # 清除缓存
        cache.clear()
        
        # 清除所有已存在的Language实例
        Language.objects.all().delete()
        
        # 创建测试管理员用户
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # 创建测试语言
        self.en_language = Language.objects.create(
            code='en',
            name='English',
            is_active=True,
            is_default=True
        )
        
        # 创建客户端
        self.client = Client()
    
    def test_language_management_page_access(self):
        """测试语言管理页面访问权限"""
        # 未登录状态应重定向
        response = self.client.get(reverse('games:admin_language_management'))
        self.assertEqual(response.status_code, 302)
        
        # 管理员登录
        self.client.login(username='admin', password='adminpassword')
        
        # 登录后应可以访问
        response = self.client.get(reverse('games:admin_language_management'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/language_management.html')
    
    def test_add_language(self):
        """测试添加新语言功能"""
        # 管理员登录
        self.client.login(username='admin', password='adminpassword')
        
        # 添加法语
        response = self.client.post(reverse('games:admin_language_management'), {
            'action': 'add_language',
            'language_name': 'Français',
            'language_code': 'fr',
            'language_active': 'on'
        })
        
        # 应该重定向回语言管理页面
        self.assertEqual(response.status_code, 302)
        
        # 验证法语已添加到数据库
        fr_language = Language.objects.filter(code='fr').first()
        self.assertIsNotNone(fr_language)
        self.assertEqual(fr_language.name, 'Français')
        self.assertTrue(fr_language.is_active)
        self.assertFalse(fr_language.is_default)


class BrowserLanguageDetectionTest(TestCase):
    """测试浏览器语言检测功能"""
    
    def setUp(self):
        # 清除缓存
        cache.clear()
        
        # 清除所有已存在的Language实例
        Language.objects.all().delete()
        
        # 创建测试语言
        self.en_language = Language.objects.create(
            code='en',
            name='English',
            is_active=True,
            is_default=True
        )
        self.zh_language = Language.objects.create(
            code='zh',
            name='中文',
            is_active=True,
            is_default=False
        )
        self.fr_language = Language.objects.create(
            code='fr',
            name='Français',
            is_active=True,
            is_default=False
        )
        
        # 创建网站设置
        self.website_settings = WebsiteSetting.objects.create(
            site_name='Test Site',
            site_description='Test Description',
            auto_detect_language=True
        )
        
        # 创建客户端
        self.client = Client()
    
    def test_browser_language_detection(self):
        """测试浏览器语言检测功能"""
        # 模拟首次访问，指定浏览器语言为法语
        response = self.client.get(
            reverse('games:home'),
            HTTP_ACCEPT_LANGUAGE='fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
        )
        
        # 应该重定向到法语版本
        self.assertEqual(response.status_code, 302)
        self.assertIn('/fr/', response.url)
        
        # 模拟首次访问，指定浏览器语言为未支持的语言
        response = self.client.get(
            reverse('games:home'),
            HTTP_ACCEPT_LANGUAGE='de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
        )
        
        # 应该使用默认语言（英语）
        self.assertEqual(response.status_code, 200)


class TranslationManagementViewTest(TestCase):
    """测试翻译管理视图功能"""
    
    def setUp(self):
        # 清除缓存
        cache.clear()
        
        # 清除所有已存在的Language实例
        Language.objects.all().delete()
        
        # 创建测试管理员用户
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # 创建测试语言
        self.en_language = Language.objects.create(
            code='en',
            name='English',
            is_active=True,
            is_default=True
        )
        self.zh_language = Language.objects.create(
            code='zh',
            name='中文',
            is_active=True,
            is_default=False
        )
        
        # 创建客户端
        self.client = Client()
    
    def test_translation_management_page_access(self):
        """测试翻译管理页面访问权限"""
        # 未登录状态应重定向
        response = self.client.get(reverse('games:admin_translation_management'))
        self.assertEqual(response.status_code, 302)
        
        # 管理员登录
        self.client.login(username='admin', password='adminpassword')
        
        # 登录后应可以访问
        response = self.client.get(reverse('games:admin_translation_management'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/translation_management.html') 