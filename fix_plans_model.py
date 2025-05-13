#!/usr/bin/env python
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

# 导入必要的模块
from django.db import connection

# 检查并添加updated_at列
with connection.cursor() as cursor:
    # 检查列是否存在
    cursor.execute("PRAGMA table_info(plans_plan)")
    columns = [info[1] for info in cursor.fetchall()]
    
    # 如果updated_at列不存在则添加
    if 'updated_at' not in columns:
        print("添加 updated_at 列到 plans_plan 表...")
        cursor.execute("ALTER TABLE plans_plan ADD COLUMN updated_at datetime DEFAULT CURRENT_TIMESTAMP")
        print("列已添加!")
    else:
        print("updated_at 列已存在，无需添加")

    # 检查是否有默认计划，使用双引号来引用保留关键字
    cursor.execute('SELECT COUNT(*) FROM plans_plan WHERE "default" = 1')
    has_default = cursor.fetchone()[0] > 0
    
    if not has_default:
        # 创建一个默认计划
        print("创建默认会员计划...")
        cursor.execute("""
        INSERT INTO plans_plan (
            "order", name, description, "default", available, visible, created, url
        ) VALUES (
            1, '基础会员', '基础会员计划', 1, 1, 1, datetime('now'), 'basic'
        )
        """)
        print("默认计划已创建!")
    else:
        print("已有默认计划，无需创建")

print("修复完成！") 