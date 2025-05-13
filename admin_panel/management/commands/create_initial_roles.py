from django.core.management.base import BaseCommand
from admin_panel.admin_user import Role, Permission
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '创建初始角色数据'

    def handle(self, *args, **options):
        # 预定义角色列表
        roles = [
            {
                'name': '超级管理员',
                'description': '拥有所有权限的超级管理员角色',
                'permissions': '*'  # 特殊标记，表示所有权限
            },
            {
                'name': '内容管理员',
                'description': '负责管理网站内容的角色',
                'permissions': ['view_article', 'add_article', 'edit_article', 'delete_article', 'publish_article']
            },
            {
                'name': '游戏管理员',
                'description': '负责管理游戏的角色',
                'permissions': ['view_game', 'add_game', 'edit_game', 'delete_game', 'publish_game', 'unpublish_game']
            },
            {
                'name': '用户管理员',
                'description': '负责管理用户账号的角色',
                'permissions': ['view_user', 'add_user', 'edit_user', 'block_user', 'unblock_user']
            },
            {
                'name': '只读管理员',
                'description': '只有查看权限的管理员角色',
                'permissions': ['view_article', 'view_game', 'view_user', 'view_setting', 'view_logs']
            }
        ]
        
        # 获取所有权限
        all_permissions = Permission.objects.all()
        
        # 计数器
        created_count = 0
        updated_count = 0
        
        # 创建角色
        for role_data in roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'is_active': True
                }
            )
            
            # 清除现有权限
            role.permissions.clear()
            
            # 添加权限
            if role_data['permissions'] == '*':
                # 添加所有权限
                role.permissions.add(*all_permissions)
            else:
                # 添加指定权限
                perms = Permission.objects.filter(codename__in=role_data['permissions'])
                role.permissions.add(*perms)
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} roles, updated {updated_count} existing roles.')) 