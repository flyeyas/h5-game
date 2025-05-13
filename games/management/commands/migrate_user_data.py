from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from games.models import FrontUser, UserProfile

class Command(BaseCommand):
    help = '将FrontUser数据迁移到auth.User和UserProfile'

    def handle(self, *args, **options):
        # 获取所有前台用户
        front_users = FrontUser.objects.all()
        self.stdout.write(f"找到 {front_users.count()} 个FrontUser记录")
        
        # 遍历前台用户并创建或更新相应的auth.User和UserProfile
        for front_user in front_users:
            # 检查是否已存在同名用户
            try:
                # 先尝试获取
                user = User.objects.get(username=front_user.username)
                self.stdout.write(f"使用现有User: {user.username}")
            except User.DoesNotExist:
                # 如果不存在则创建
                user = User.objects.create_user(
                    username=front_user.username,
                    email=front_user.email,
                    password=None  # 不设置密码，保持原样
                )
                # 直接设置加密后的密码
                user.password = front_user.password
                user.is_staff = front_user.is_staff
                user.is_active = front_user.is_active
                user.date_joined = front_user.date_joined
                user.last_login = front_user.last_login
                user.save()
                self.stdout.write(f"创建新User: {user.username}")
            
            # 获取或创建用户资料
            profile, created = UserProfile.objects.get_or_create(
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
            
            if created:
                self.stdout.write(f"创建新UserProfile: {user.username}")
            else:
                # 更新现有资料
                profile.avatar = front_user.avatar
                profile.bio = front_user.bio
                profile.is_member = front_user.is_member
                profile.member_until = front_user.member_until
                profile.member_type = front_user.member_type
                profile.email_notifications = front_user.email_notifications
                profile.game_updates = front_user.game_updates
                profile.subscription_alerts = front_user.subscription_alerts
                profile.marketing_emails = front_user.marketing_emails
                profile.profile_visibility = front_user.profile_visibility
                profile.game_history_visibility = front_user.game_history_visibility
                profile.data_collection = front_user.data_collection
                profile.membership_status = front_user.membership_status
                profile.membership_start_date = front_user.membership_start_date
                profile.membership_renewal_date = front_user.membership_renewal_date
                profile.billing_cycle = front_user.billing_cycle
                profile.is_premium = front_user.is_premium
                profile.role = front_user.role
                profile.social_links = front_user.social_links
                profile.preferences = front_user.preferences
                profile.save()
                self.stdout.write(f"更新现有UserProfile: {user.username}")
                
        self.stdout.write(self.style.SUCCESS('用户数据迁移完成！')) 