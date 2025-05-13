from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger('admin_panel')

class Command(BaseCommand):
    """
    测试用户认证的管理命令
    
    该命令用于测试用户凭据是否有效，输出认证结果和用户信息。
    可用于验证密码是否被正确设置或更改。
    """
    
    help = '测试用户认证'

    def add_arguments(self, parser):
        """
        添加命令行参数
        
        Args:
            parser: 命令行参数解析器
        """
        parser.add_argument('--username', type=str, required=True, help='用户名')
        parser.add_argument('--password', type=str, required=True, help='密码')

    def handle(self, *args, **options):
        """
        执行命令的主入口点
        
        使用提供的用户名和密码尝试进行认证，输出认证结果。
        
        Args:
            options: 命令行参数字典，包含username和password
        """
        username = options['username']
        password = options['password']
        
        # 尝试认证
        user = authenticate(username=username, password=password)
        
        if user is not None:
            self.stdout.write(self.style.SUCCESS(f'认证成功! 用户 {username} 验证通过'))
            self.stdout.write(f'用户ID: {user.id}')
            self.stdout.write(f'用户名: {user.username}')
            self.stdout.write(f'邮箱: {user.email}')
            self.stdout.write(f'是否超级管理员: {user.is_superuser}')
            self.stdout.write(f'是否管理员: {user.is_staff}')
            
            logger.info(f'用户 {username} 认证测试成功')
            return
        else:
            self.stdout.write(self.style.ERROR(f'认证失败! 用户名或密码不正确'))
            logger.warning(f'用户 {username} 认证测试失败')
            return 