from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from admin_panel.admin_user import AdminProfile

class AdminUserProtectionTest(TestCase):
    """测试超级管理员保护机制"""

    def setUp(self):
        """测试前准备"""
        # 创建ID为1的超级管理员用户
        self.admin_user = User.objects.create_superuser(
            id=1,
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        # 创建管理员资料
        self.admin_profile = AdminProfile.objects.create(
            user=self.admin_user,
            role=10,
            status='active',
            real_name='测试管理员'
        )
        
        # 创建普通用户（用于对比测试）
        self.normal_user = User.objects.create_user(
            username='normal',
            email='normal@example.com',
            password='normal123'
        )

    def test_admin_user_exists(self):
        """测试超级管理员是否成功创建"""
        admin = User.objects.get(id=1)
        self.assertEqual(admin.username, 'admin')
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        
        # 测试管理员资料
        self.assertEqual(admin.admin_profile.role, 10)
        self.assertEqual(admin.admin_profile.status, 'active')

    def test_admin_user_protection(self):
        """测试超级管理员删除保护"""
        # 普通用户可以删除
        normal = User.objects.get(username='normal')
        normal.delete()
        self.assertEqual(User.objects.filter(username='normal').exists(), False)
        
        # 尝试删除超级管理员
        admin = User.objects.get(id=1)
        with self.assertRaises(PermissionDenied):
            admin.delete() 