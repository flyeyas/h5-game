from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from admin_panel.menu import Menu


class Command(BaseCommand):
    help = '更新后台菜单项，添加前台用户管理链接'

    def handle(self, *args, **options):
        # 检查是否存在用户管理主菜单
        user_menu, created = Menu.objects.get_or_create(
            name='用户管理',
            defaults={
                'url': '#',
                'icon': 'fas fa-users',
                'parent': None,
                'order': 20,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('创建用户管理主菜单成功'))
        
        # 添加前台用户管理菜单项
        front_user_menu, created = Menu.objects.get_or_create(
            name='前台用户管理',
            parent=user_menu,
            defaults={
                'url': '/admin/front-users/',
                'icon': 'fas fa-user-friends',
                'order': 20,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('创建前台用户管理菜单项成功'))
        else:
            # 更新URL以确保它是正确的
            front_user_menu.url = '/admin/front-users/'
            front_user_menu.save()
            self.stdout.write(self.style.SUCCESS('更新前台用户管理菜单项成功'))
            
        # 检查是否存在管理员用户管理菜单项
        admin_user_menu, created = Menu.objects.get_or_create(
            name='管理员用户',
            parent=user_menu,
            defaults={
                'url': '/admin/users/',
                'icon': 'fas fa-user-shield',
                'order': 10,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('创建管理员用户菜单项成功'))
        
        self.stdout.write(self.style.SUCCESS('菜单项更新完成')) 