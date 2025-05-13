# Generated manually
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

def forward_user_data(apps, schema_editor):
    # 获取模型
    FrontUser = apps.get_model('games', 'FrontUser')
    User = apps.get_model('auth', 'User')
    FrontGameFavorite = apps.get_model('games', 'FrontGameFavorite')
    FrontGameHistory = apps.get_model('games', 'FrontGameHistory')
    FrontGameComment = apps.get_model('games', 'FrontGameComment')
    Transaction = apps.get_model('games', 'Transaction')
    UserProfile = apps.get_model('games', 'UserProfile')
    
    # 为每个FrontUser创建或获取对应的auth.User
    frontuser_to_user = {}
    for front_user in FrontUser.objects.all():
        # 检查是否已存在同名用户
        user, created = User.objects.get_or_create(
            username=front_user.username,
            defaults={
                'email': front_user.email,
                'password': front_user.password,
                'is_staff': front_user.is_staff,
                'is_active': front_user.is_active,
                'date_joined': front_user.date_joined,
                'last_login': front_user.last_login
            }
        )
        
        # 创建用户资料
        profile, created_profile = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'avatar': front_user.avatar,
                'bio': front_user.bio,
                'is_member': front_user.is_member,
                'member_until': front_user.member_until,
                'member_type': front_user.member_type,
                'email_notifications': front_user.email_notifications,
                'game_updates': front_user.game_updates,
                'subscription_alerts': front_user.subscription_alerts,
                'marketing_emails': front_user.marketing_emails,
                'profile_visibility': front_user.profile_visibility,
                'game_history_visibility': front_user.game_history_visibility,
                'data_collection': front_user.data_collection,
                'membership_status': front_user.membership_status,
                'membership_start_date': front_user.membership_start_date,
                'membership_renewal_date': front_user.membership_renewal_date,
                'billing_cycle': front_user.billing_cycle,
                'is_premium': front_user.is_premium,
                'role': front_user.role,
                'social_links': front_user.social_links,
                'preferences': front_user.preferences
            }
        )
        
        # 保存映射关系
        frontuser_to_user[front_user.id] = user.id
    
    # 暂时清空关联表中的数据，以避免外键冲突
    # 这些数据将在下一阶段中重新创建
    FrontGameFavorite.objects.all().delete()
    FrontGameHistory.objects.all().delete()
    FrontGameComment.objects.all().delete()
    Transaction.objects.all().delete()

def reverse_user_data(apps, schema_editor):
    # 此函数不做任何事情，因为数据已被删除
    pass

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('games', '0019_alter_frontgamecomment_user_and_more'),
    ]

    operations = [
        migrations.RunPython(forward_user_data, reverse_user_data),
    ] 