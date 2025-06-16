# Generated manually to fix permissions language

from django.db import migrations


def fix_permissions_language(apps, schema_editor):
    """Fix Chinese names in permission data by translating them to English"""
    Permission = apps.get_model('auth', 'Permission')

    # Define Chinese to English mapping
    permission_translations = {
        # Game-related permissions
        'Can add 游戏': 'Can add game',
        'Can change 游戏': 'Can change game',
        'Can delete 游戏': 'Can delete game',
        'Can view 游戏': 'Can view game',

        # Category-related permissions
        'Can add 游戏分类': 'Can add category',
        'Can change 游戏分类': 'Can change category',
        'Can delete 游戏分类': 'Can delete category',
        'Can view 游戏分类': 'Can view category',

        # Advertisement-related permissions
        'Can add 广告': 'Can add advertisement',
        'Can change 广告': 'Can change advertisement',
        'Can delete 广告': 'Can delete advertisement',
        'Can view 广告': 'Can view advertisement',

        # User profile-related permissions (if exists)
        'Can add 用户资料': 'Can add user profile',
        'Can change 用户资料': 'Can change user profile',
        'Can delete 用户资料': 'Can delete user profile',
        'Can view 用户资料': 'Can view user profile',
    }

    # Iterate through all permissions and update Chinese names
    for permission in Permission.objects.all():
        if permission.name in permission_translations:
            permission.name = permission_translations[permission.name]
            permission.save()


def reverse_fix_permissions_language(apps, schema_editor):
    """Rollback operation: change English permission names back to Chinese (if needed)"""
    Permission = apps.get_model('auth', 'Permission')

    # Define English to Chinese mapping (for rollback)
    reverse_translations = {
        # Game-related permissions
        'Can add game': 'Can add 游戏',
        'Can change game': 'Can change 游戏',
        'Can delete game': 'Can delete 游戏',
        'Can view game': 'Can view 游戏',

        # Category-related permissions
        'Can add category': 'Can add 游戏分类',
        'Can change category': 'Can change 游戏分类',
        'Can delete category': 'Can delete 游戏分类',
        'Can view category': 'Can view 游戏分类',

        # Advertisement-related permissions
        'Can add advertisement': 'Can add 广告',
        'Can change advertisement': 'Can change 广告',
        'Can delete advertisement': 'Can delete 广告',
        'Can view advertisement': 'Can view 广告',

        # User profile-related permissions
        'Can add user profile': 'Can add 用户资料',
        'Can change user profile': 'Can change 用户资料',
        'Can delete user profile': 'Can delete 用户资料',
        'Can view user profile': 'Can view 用户资料',
    }

    # Iterate through all permissions and rollback to Chinese names
    for permission in Permission.objects.all():
        if permission.name in reverse_translations:
            permission.name = reverse_translations[permission.name]
            permission.save()


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0004_auto_20250616_0234'),
    ]

    operations = [
        migrations.RunPython(
            fix_permissions_language,
            reverse_fix_permissions_language,
        ),
    ]
