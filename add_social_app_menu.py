#!/usr/bin/env python
import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

# 导入模型
from admin_panel.menu import Menu

def add_social_app_menu():
    # 查找设置相关的菜单项
    try:
        # 尝试查找"设置"菜单
        settings_menu = Menu.objects.filter(name__in=['设置', '网站设置', 'Settings', '系统设置']).first()
        
        if not settings_menu:
            # 如果找不到，创建一个顶级的"系统设置"菜单
            settings_menu = Menu.objects.create(
                name='系统设置',
                url='#',
                icon='fas fa-cogs',
                parent=None,
                order=100,
                is_active=True
            )
            print(f'创建了顶级菜单: {settings_menu.name}, ID={settings_menu.id}')
        else:
            print(f'找到现有设置菜单: {settings_menu.name}, ID={settings_menu.id}')
            
        # 检查是否已存在社交应用菜单
        social_app_menu = Menu.objects.filter(name__in=['社交应用管理', 'Social Apps']).first()
        
        if not social_app_menu:
            # 创建社交应用菜单
            social_app_menu = Menu.objects.create(
                name='社交应用管理',
                url='/admin/social-apps/',
                icon='fas fa-share-alt',
                parent=settings_menu,
                order=60,  # 放在站点管理之后
                is_active=True
            )
            print(f'创建了社交应用菜单: {social_app_menu.name}, ID={social_app_menu.id}, 父菜单={settings_menu.name}')
        else:
            print(f'社交应用菜单已存在: {social_app_menu.name}, ID={social_app_menu.id}')
            
        return True
    except Exception as e:
        print(f'添加菜单失败: {str(e)}')
        return False

if __name__ == '__main__':
    print('开始添加社交应用菜单...')
    result = add_social_app_menu()
    if result:
        print('社交应用菜单添加成功！')
    else:
        print('社交应用菜单添加失败！') 