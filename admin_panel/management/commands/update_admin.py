from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import logging

logger = logging.getLogger('admin_panel')

class Command(BaseCommand):
    """
    更新ID为1的超级管理员用户信息的管理命令
    
    该命令用于将ID为1的超级管理员信息更新为指定的用户名、邮箱和密码。
    这是一次性操作，用于初始化或需要特定变更时执行。
    """
    
    help = '更新ID为1的超级管理员用户的用户名、邮箱和密码'

    def add_arguments(self, parser):
        """
        添加命令行参数
        
        Args:
            parser: 命令行参数解析器
        """
        parser.add_argument('--username', type=str, required=True, help='新的用户名')
        parser.add_argument('--email', type=str, required=True, help='新的邮箱地址')
        parser.add_argument('--password', type=str, required=True, help='新的密码')

    def handle(self, *args, **options):
        """
        执行命令的主入口点
        
        查找ID为1的用户，并将其信息更新为命令行提供的值
        
        Args:
            options: 命令行参数字典，包含username, email和password
        """
        username = options['username']
        email = options['email']
        password = options['password']
        
        try:
            # 查找ID为1的用户
            try:
                user = User.objects.get(id=1)
                self.stdout.write(self.style.SUCCESS(f'找到ID为1的用户: {user.username}'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'ID为1的用户不存在，请先运行init_admin_user命令'))
                return

            # 记录旧信息
            old_username = user.username
            old_email = user.email

            # 更新用户信息
            user.username = username
            user.email = email
            user.password = make_password(password)  # 安全地设置密码
            user.save()

            self.stdout.write(self.style.SUCCESS(f'已更新ID为1的用户信息:'))
            self.stdout.write(f'用户名: {old_username} -> {user.username}')
            self.stdout.write(f'邮箱: {old_email} -> {user.email}')
            self.stdout.write(f'密码已更新')
            
            logger.info(f'ID为1的超级管理员信息已更新: username={user.username}, email={user.email}')
            
        except Exception as e:
            logger.error(f'更新超级管理员信息失败: {str(e)}')
            raise CommandError(f'更新超级管理员信息失败: {str(e)}') 