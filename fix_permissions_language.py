#!/usr/bin/env python
"""
修复权限数据中的中文名称，将其翻译为英文
这个脚本将更新数据库中已存在的权限数据，将中文名称改为英文
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'html5games.settings')
django.setup()

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

def fix_permissions_language():
    """修复权限数据中的中文名称"""
    
    # 定义中文到英文的映射
    permission_translations = {
        # 游戏相关权限
        'Can add 游戏': 'Can add game',
        'Can change 游戏': 'Can change game', 
        'Can delete 游戏': 'Can delete game',
        'Can view 游戏': 'Can view game',
        
        # 分类相关权限
        'Can add 游戏分类': 'Can add category',
        'Can change 游戏分类': 'Can change category',
        'Can delete 游戏分类': 'Can delete category', 
        'Can view 游戏分类': 'Can view category',
        
        # 广告相关权限
        'Can add 广告': 'Can add advertisement',
        'Can change 广告': 'Can change advertisement',
        'Can delete 广告': 'Can delete advertisement',
        'Can view 广告': 'Can view advertisement',
        
        # 用户资料相关权限（如果存在）
        'Can add 用户资料': 'Can add user profile',
        'Can change 用户资料': 'Can change user profile',
        'Can delete 用户资料': 'Can delete user profile',
        'Can view 用户资料': 'Can view user profile',
    }
    
    print("Starting to fix Chinese names in permission data...")

    updated_count = 0

    # Iterate through all permissions
    for permission in Permission.objects.all():
        if permission.name in permission_translations:
            old_name = permission.name
            new_name = permission_translations[old_name]

            print(f"Updating permission: '{old_name}' -> '{new_name}'")

            permission.name = new_name
            permission.save()
            updated_count += 1

    print(f"\nPermission fix completed! Updated {updated_count} permissions in total.")

    # Display current status of all permissions
    print("\nCurrent permission list:")
    print("-" * 80)
    for permission in Permission.objects.all().order_by('content_type__app_label', 'content_type__model', 'codename'):
        content_type = permission.content_type
        print(f"ID: {permission.id:2d} | {content_type.app_label:12s} | {content_type.model:15s} | {permission.name}")

def check_chinese_permissions():
    """Check if there are still permissions containing Chinese characters"""
    print("\nChecking for permissions still containing Chinese characters...")

    chinese_permissions = []
    for permission in Permission.objects.all():
        # Check if contains Chinese characters
        if any('\u4e00' <= char <= '\u9fff' for char in permission.name):
            chinese_permissions.append(permission)

    if chinese_permissions:
        print(f"Found {len(chinese_permissions)} permissions still containing Chinese:")
        for perm in chinese_permissions:
            print(f"  - ID: {perm.id}, Name: {perm.name}, Codename: {perm.codename}")
    else:
        print("✅ All permission names have been successfully converted to English!")

if __name__ == '__main__':
    try:
        fix_permissions_language()
        check_chinese_permissions()
        print("\nPermission language fix script execution completed!")
    except Exception as e:
        print(f"Error occurred during execution: {e}")
        sys.exit(1)
