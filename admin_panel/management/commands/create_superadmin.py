from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from admin_panel.models import AdminUser

class Command(BaseCommand):
    help = '创建一个超级管理员账号'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='管理员用户名')
        parser.add_argument('--password', type=str, default='admin123', help='管理员密码')
        parser.add_argument('--email', type=str, default='admin@example.com', help='管理员邮箱')
        parser.add_argument('--real_name', type=str, default='超级管理员', help='管理员姓名')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        real_name = options['real_name']

        # 检查用户是否已存在
        if AdminUser.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'用户名 "{username}" 已存在'))
            return

        # 创建超级管理员
        admin = AdminUser.objects.create(
            username=username,
            password=make_password(password),  # 确保密码被正确加密
            email=email,
            real_name=real_name,
            role='super_admin',  # 设置为超级管理员角色
            status='active',  # 设置为活跃状态
            is_staff=True,  # 可以访问管理后台
            is_superuser=True,  # 拥有所有权限
            created_time=timezone.now(),
        )

        self.stdout.write(self.style.SUCCESS(f'成功创建超级管理员: {username}'))
        self.stdout.write(self.style.SUCCESS(f'用户名: {username}'))
        self.stdout.write(self.style.SUCCESS(f'密码: {password}'))
        self.stdout.write(self.style.SUCCESS(f'请使用以上信息登录后台管理系统'))