#!/usr/bin/env python
import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

# 导入模型
from admin_panel.menu import Menu

def add_sites_menu():
    # 查找设置相关的菜单项
    try:
        # 尝试查找"设置"菜单
        settings_menu = Menu.objects.filter(name__in=['设置', '网站设置', 'Settings']).first()
        
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
            
        # 检查是否已存在 Sites 菜单
        sites_menu = Menu.objects.filter(name__in=['站点管理', 'Sites']).first()
        
        if not sites_menu:
            # 创建 Sites 菜单
            sites_menu = Menu.objects.create(
                name='站点管理',
                url='/admin/sites/',
                icon='fas fa-globe',
                parent=settings_menu,
                order=50,
                is_active=True
            )
            print(f'创建了 Sites 菜单: {sites_menu.name}, ID={sites_menu.id}, 父菜单={settings_menu.name}')
        else:
            print(f'Sites 菜单已存在: {sites_menu.name}, ID={sites_menu.id}')
            
        return True
    except Exception as e:
        print(f'添加菜单失败: {str(e)}')
        return False

if __name__ == '__main__':
    print('开始添加 Sites 菜单...')
    result = add_sites_menu()
    if result:
        print('Sites 菜单添加成功！')
    else:
        print('Sites 菜单添加失败！') 