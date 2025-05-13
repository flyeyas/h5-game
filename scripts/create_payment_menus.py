#!/usr/bin/env python
"""
此脚本用于创建支付网关相关的菜单项
使用方法：
python manage.py shell < scripts/create_payment_menus.py
"""

import os
import sys
import django
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

# 导入Menu模型
from admin_panel.menu import Menu

# 定义支付网关管理主菜单
payment_gateway_menu = {
    'name': '支付网关管理',
    'url': '/admin/payment-gateway/',
    'icon': 'fas fa-credit-card',
    'parent': None,
    'order': 30,
    'is_active': True
}

# 定义子菜单项
children = [
    {
        'name': '网关管理',
        'url': '/admin/payment-gateway/',
        'icon': 'fas fa-cogs',
        'order': 1,
        'is_active': True
    },
    {
        'name': 'PayPal配置',
        'url': '/admin/payment-gateway/paypal/',
        'icon': 'fab fa-paypal',
        'order': 2,
        'is_active': True
    },
    {
        'name': '支付宝配置',
        'url': '/admin/payment-gateway/alipay/',
        'icon': 'fas fa-yen-sign',
        'order': 3,
        'is_active': True
    },
    {
        'name': '微信支付配置',
        'url': '/admin/payment-gateway/wechatpay/',
        'icon': 'fab fa-weixin',
        'order': 4,
        'is_active': True
    },
    {
        'name': 'Stripe配置',
        'url': '/admin/payment-gateway/stripe/',
        'icon': 'fab fa-stripe-s',
        'order': 5,
        'is_active': True
    },
    {
        'name': 'Braintree配置',
        'url': '/admin/payment-gateway/braintree/',
        'icon': 'fas fa-money-check-alt',
        'order': 6,
        'is_active': True
    },
    {
        'name': 'Adyen配置',
        'url': '/admin/payment-gateway/adyen/',
        'icon': 'fas fa-money-bill-wave',
        'order': 7,
        'is_active': True
    },
    {
        'name': '会员价格',
        'url': '/admin/payment-gateway/membership-price/',
        'icon': 'fas fa-tags',
        'order': 8,
        'is_active': True
    },
    {
        'name': '交易记录',
        'url': '/admin/payment-gateway/transactions/',
        'icon': 'fas fa-receipt',
        'order': 9,
        'is_active': True
    }
]

def create_or_update_menu():
    """创建或更新菜单"""
    print("开始创建或更新菜单项...")
    
    # 创建或更新主菜单
    parent_menu, created = Menu.objects.get_or_create(
        name=payment_gateway_menu['name'],
        defaults={
            'url': payment_gateway_menu['url'],
            'icon': payment_gateway_menu['icon'],
            'parent': payment_gateway_menu['parent'],
            'order': payment_gateway_menu['order'],
            'is_active': payment_gateway_menu['is_active']
        }
    )
    
    if created:
        print(f"创建支付网关管理主菜单 '{payment_gateway_menu['name']}' 成功")
    else:
        # 更新菜单信息
        parent_menu.url = payment_gateway_menu['url']
        parent_menu.icon = payment_gateway_menu['icon']
        parent_menu.order = payment_gateway_menu['order']
        parent_menu.is_active = payment_gateway_menu['is_active']
        parent_menu.save()
        print(f"更新支付网关管理主菜单 '{payment_gateway_menu['name']}' 成功")
    
    # 创建或更新子菜单
    for child in children:
        child_menu, created = Menu.objects.get_or_create(
            name=child['name'],
            parent=parent_menu,
            defaults={
                'url': child['url'],
                'icon': child['icon'],
                'order': child['order'],
                'is_active': child['is_active']
            }
        )
        
        if created:
            print(f"创建菜单项 '{child['name']}' 成功")
        else:
            # 更新菜单信息
            child_menu.url = child['url']
            child_menu.icon = child['icon']
            child_menu.order = child['order']
            child_menu.is_active = child['is_active']
            child_menu.save()
            print(f"更新菜单项 '{child['name']}' 成功")
    
    print("菜单项创建或更新完成")

if __name__ == '__main__':
    create_or_update_menu() 