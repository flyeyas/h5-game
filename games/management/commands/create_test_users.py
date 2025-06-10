from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = '批量创建测试用户'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            type=int,
            default=4,
            help='开始的用户编号（默认从4开始，因为testuser1-3已存在）'
        )
        parser.add_argument(
            '--end',
            type=int,
            default=20,
            help='结束的用户编号（默认到20）'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='用户密码（默认：testpass123）'
        )

    def handle(self, *args, **options):
        start = options['start']
        end = options['end']
        password = options['password']
        
        created_users = []
        skipped_users = []
        
        with transaction.atomic():
            for i in range(start, end + 1):
                username = f'testuser{i}'
                email = f'testuser{i}@example.com'
                
                # 检查用户是否已存在
                if User.objects.filter(username=username).exists():
                    skipped_users.append(username)
                    self.stdout.write(
                        self.style.WARNING(f'用户 {username} 已存在，跳过创建')
                    )
                    continue
                
                try:
                    # 创建用户
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        is_active=True,
                        is_staff=False,
                        is_superuser=False
                    )
                    created_users.append(username)
                    self.stdout.write(
                        self.style.SUCCESS(f'成功创建用户: {username}')
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'创建用户 {username} 失败: {str(e)}')
                    )
        
        # 输出总结
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'创建完成！')
        self.stdout.write(f'成功创建用户数量: {len(created_users)}')
        self.stdout.write(f'跳过用户数量: {len(skipped_users)}')
        
        if created_users:
            self.stdout.write('\n成功创建的用户:')
            for username in created_users:
                self.stdout.write(f'  - {username}')
        
        if skipped_users:
            self.stdout.write('\n跳过的用户:')
            for username in skipped_users:
                self.stdout.write(f'  - {username}')
        
        self.stdout.write('\n所有用户的默认密码: ' + password)
        self.stdout.write('='*50)
