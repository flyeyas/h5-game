from django.core.management.base import BaseCommand
from admin_panel.admin_user import Permission
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '创建初始权限数据'

    def handle(self, *args, **options):
        # 预定义权限列表
        permissions = [
            # 内容管理权限
            {'name': '查看文章', 'codename': 'view_article', 'category': 'content', 'description': '查看所有文章的权限'},
            {'name': '添加文章', 'codename': 'add_article', 'category': 'content', 'description': '添加新文章的权限'},
            {'name': '编辑文章', 'codename': 'edit_article', 'category': 'content', 'description': '编辑现有文章的权限'},
            {'name': '删除文章', 'codename': 'delete_article', 'category': 'content', 'description': '删除文章的权限'},
            {'name': '发布文章', 'codename': 'publish_article', 'category': 'content', 'description': '将文章状态改为已发布的权限'},
            
            # 游戏管理权限
            {'name': '查看游戏', 'codename': 'view_game', 'category': 'game', 'description': '查看所有游戏的权限'},
            {'name': '添加游戏', 'codename': 'add_game', 'category': 'game', 'description': '添加新游戏的权限'},
            {'name': '编辑游戏', 'codename': 'edit_game', 'category': 'game', 'description': '编辑现有游戏的权限'},
            {'name': '删除游戏', 'codename': 'delete_game', 'category': 'game', 'description': '删除游戏的权限'},
            {'name': '发布游戏', 'codename': 'publish_game', 'category': 'game', 'description': '将游戏状态改为已发布的权限'},
            {'name': '下线游戏', 'codename': 'unpublish_game', 'category': 'game', 'description': '将游戏下线的权限'},
            
            # 用户管理权限
            {'name': '查看用户', 'codename': 'view_user', 'category': 'user', 'description': '查看所有用户的权限'},
            {'name': '添加用户', 'codename': 'add_user', 'category': 'user', 'description': '添加新用户的权限'},
            {'name': '编辑用户', 'codename': 'edit_user', 'category': 'user', 'description': '编辑现有用户的权限'},
            {'name': '删除用户', 'codename': 'delete_user', 'category': 'user', 'description': '删除用户的权限'},
            {'name': '封禁用户', 'codename': 'block_user', 'category': 'user', 'description': '封禁用户的权限'},
            {'name': '解封用户', 'codename': 'unblock_user', 'category': 'user', 'description': '解封用户的权限'},
            
            # 系统设置权限
            {'name': '查看设置', 'codename': 'view_setting', 'category': 'system', 'description': '查看系统设置的权限'},
            {'name': '修改设置', 'codename': 'edit_setting', 'category': 'system', 'description': '修改系统设置的权限'},
            {'name': '管理员管理', 'codename': 'manage_admin', 'category': 'system', 'description': '管理管理员账号的权限'},
            {'name': '角色管理', 'codename': 'manage_roles', 'category': 'system', 'description': '管理角色和权限的权限'},
            {'name': '查看日志', 'codename': 'view_logs', 'category': 'system', 'description': '查看系统日志的权限'},
        ]
        
        # 计数器
        created_count = 0
        existing_count = 0
        
        # 创建权限
        for perm_data in permissions:
            perm, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults={
                    'name': perm_data['name'],
                    'category': perm_data['category'],
                    'description': perm_data['description']
                }
            )
            
            if created:
                created_count += 1
            else:
                existing_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} permissions, {existing_count} already existed.')) 