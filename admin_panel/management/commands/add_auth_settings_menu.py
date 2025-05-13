from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from admin_panel.menu import Menu
from django.urls import reverse


class Command(BaseCommand):
    help = '添加认证设置菜单项到系统设置菜单'

    def handle(self, *args, **options):
        # 检查是否存在系统设置主菜单
        settings_menu = Menu.objects.filter(name='系统设置').first()
        
        if settings_menu:
            # 添加认证设置菜单项
            auth_settings_menu, created = Menu.objects.get_or_create(
                name='认证设置',
                parent=settings_menu,
                defaults={
                    'url': '/admin/auth-settings/',
                    'icon': 'fas fa-user-lock',
                    'order': 25,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('创建认证设置菜单项成功'))
            else:
                # 更新URL以确保它是正确的
                auth_settings_menu.url = '/admin/auth-settings/'
                auth_settings_menu.save()
                self.stdout.write(self.style.SUCCESS('更新认证设置菜单项成功'))
        else:
            self.stdout.write(self.style.ERROR('系统设置菜单不存在，请先创建系统设置菜单'))
            
        self.stdout.write(self.style.SUCCESS('菜单项更新完成')) 