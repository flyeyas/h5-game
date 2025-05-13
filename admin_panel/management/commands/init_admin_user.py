from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from admin_panel.admin_user import AdminProfile
from django.utils import timezone
import logging

logger = logging.getLogger('admin_panel')

class Command(BaseCommand):
    help = '确保ID为1的用户是网站超级管理员，并且禁止被删除'

    def handle(self, *args, **options):
        try:
            # 查找ID为1的用户
            try:
                user = User.objects.get(id=1)
                self.stdout.write(self.style.SUCCESS(f'找到ID为1的用户: {user.username}'))
            except User.DoesNotExist:
                # 如果不存在，创建一个超级管理员用户
                user = User.objects.create_superuser(
                    username='admin', 
                    email='admin@example.com', 
                    password='admin123'
                )
                user.id = 1
                user.save()
                self.stdout.write(self.style.SUCCESS(f'创建ID为1的超级管理员用户: {user.username}'))

            # 确保用户是超级管理员
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'已将用户 {user.username} 设置为超级管理员'))

            # 确保用户已激活
            if not user.is_active:
                user.is_active = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'已激活用户 {user.username}'))

            # 检查并创建管理员资料
            try:
                admin_profile = AdminProfile.objects.get(user=user)
                self.stdout.write(self.style.SUCCESS(f'已找到用户 {user.username} 的管理员资料'))
            except AdminProfile.DoesNotExist:
                # 创建管理员资料
                admin_profile = AdminProfile.objects.create(
                    user=user,
                    role=10,  # Super Admin
                    status='active',
                    real_name='系统管理员',
                    last_login_time=timezone.now(),
                    notes='系统初始化创建的超级管理员，此账号禁止删除'
                )
                self.stdout.write(self.style.SUCCESS(f'已为用户 {user.username} 创建管理员资料'))

            # 添加信号处理器保护此用户不被删除 (在models.py中实现)
            
            self.stdout.write(self.style.SUCCESS(f'成功设置ID为1的用户 {user.username} 为系统超级管理员'))
            
        except Exception as e:
            logger.error(f'初始化超级管理员失败: {str(e)}')
            raise CommandError(f'初始化超级管理员失败: {str(e)}') 