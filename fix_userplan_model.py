#!/usr/bin/env python
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

# 导入必要的模块
from django.db import connection

# 检查并添加需要的列到plans_userplan表
with connection.cursor() as cursor:
    # 检查列是否存在
    cursor.execute("PRAGMA table_info(plans_userplan)")
    columns = [info[1] for info in cursor.fetchall()]
    
    # 添加缺少的列
    if 'created' not in columns:
        print("添加 created 列到 plans_userplan 表...")
        cursor.execute("ALTER TABLE plans_userplan ADD COLUMN created datetime DEFAULT CURRENT_TIMESTAMP")
        print("created 列已添加!")
    
    if 'updated_at' not in columns:
        print("添加 updated_at 列到 plans_userplan 表...")
        cursor.execute("ALTER TABLE plans_userplan ADD COLUMN updated_at datetime DEFAULT CURRENT_TIMESTAMP")
        print("updated_at 列已添加!")

print("修复完成！") 