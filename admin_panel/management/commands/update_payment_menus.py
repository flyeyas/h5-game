from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from admin_panel.menu import Menu, PAYMENT_GATEWAY_MENU_ITEM


class Command(BaseCommand):
    help = '更新后台菜单项，添加支付网关配置相关链接'

    def handle(self, *args, **options):
        # 检查是否存在支付网关管理主菜单
        payment_menu, created = Menu.objects.get_or_create(
            name=PAYMENT_GATEWAY_MENU_ITEM['name'],
            defaults={
                'url': PAYMENT_GATEWAY_MENU_ITEM['url'],
                'icon': PAYMENT_GATEWAY_MENU_ITEM['icon'],
                'parent': None,
                'order': PAYMENT_GATEWAY_MENU_ITEM['order'],
                'is_active': PAYMENT_GATEWAY_MENU_ITEM['is_active']
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'创建支付网关管理主菜单 "{PAYMENT_GATEWAY_MENU_ITEM["name"]}" 成功'))
        else:
            # 更新菜单信息
            payment_menu.url = PAYMENT_GATEWAY_MENU_ITEM['url']
            payment_menu.icon = PAYMENT_GATEWAY_MENU_ITEM['icon']
            payment_menu.order = PAYMENT_GATEWAY_MENU_ITEM['order']
            payment_menu.is_active = PAYMENT_GATEWAY_MENU_ITEM['is_active']
            payment_menu.save()
            self.stdout.write(self.style.SUCCESS(f'更新支付网关管理主菜单 "{PAYMENT_GATEWAY_MENU_ITEM["name"]}" 成功'))
        
        # 添加子菜单项
        for child in PAYMENT_GATEWAY_MENU_ITEM['children']:
            child_menu, created = Menu.objects.get_or_create(
                name=child['name'],
                parent=payment_menu,
                defaults={
                    'url': child['url'],
                    'icon': child['icon'],
                    'order': child['order'],
                    'is_active': child['is_active']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'创建菜单项 "{child["name"]}" 成功'))
            else:
                # 更新菜单信息
                child_menu.url = child['url']
                child_menu.icon = child['icon']
                child_menu.order = child['order']
                child_menu.is_active = child['is_active']
                child_menu.save()
                self.stdout.write(self.style.SUCCESS(f'更新菜单项 "{child["name"]}" 成功'))
        
        self.stdout.write(self.style.SUCCESS('支付配置相关菜单项更新完成')) 