from django.db import migrations

def add_payment_menu_item(apps, schema_editor):
    """添加支付配置菜单项"""
    Menu = apps.get_model('admin_panel', 'Menu')
    
    # 检查是否已存在系统设置菜单作为父项
    system_menu = Menu.objects.filter(name='系统设置', parent__isnull=True).first()
    
    if not system_menu:
        # 创建系统设置顶级菜单
        system_menu = Menu.objects.create(
            name='系统设置',
            url='#',
            icon='fas fa-cogs',
            order=90,
            is_active=True
        )
    
    # 检查支付配置菜单是否已存在
    if not Menu.objects.filter(name='支付配置管理', url='/admin/payment-settings/').exists():
        # 创建支付配置菜单
        Menu.objects.create(
            name='支付配置管理',
            url='/admin/payment-settings/',
            icon='fas fa-credit-card',
            parent=system_menu,
            order=12,  # 放在系统配置后面
            is_active=True
        )

def remove_payment_menu_item(apps, schema_editor):
    """移除支付配置菜单项"""
    Menu = apps.get_model('admin_panel', 'Menu')
    Menu.objects.filter(name='支付配置管理', url='/admin/payment-settings/').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0002_alter_adminuser_managers_alter_adminlog_timestamp_and_more'),
    ]

    operations = [
        migrations.RunPython(add_payment_menu_item, remove_payment_menu_item),
    ] 