from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    FrontGameFavorite, FrontGameHistory, FrontGameComment,
    UserProfile
)

# 只注册本地定义的FrontUser模型，其他模型已在core/admin.py中注册
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料管理"""
    list_display = ['user', 'member_type', 'is_member', 'member_until', 'role']
    list_filter = ['is_member', 'member_type', 'role']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
    readonly_fields = ['user']
    fieldsets = (
        (_('用户信息'), {
            'fields': ('user', 'avatar', 'bio'),
        }),
        (_('会员信息'), {
            'fields': ('is_member', 'member_type', 'member_until', 'membership_status',
                      'membership_start_date', 'membership_renewal_date', 'billing_cycle'),
        }),
        (_('设置'), {
            'fields': ('email_notifications', 'game_updates', 'subscription_alerts',
                      'marketing_emails', 'profile_visibility', 'game_history_visibility',
                      'data_collection'),
        }),
        (_('权限'), {
            'fields': ('is_premium', 'role'),
        }),
    )

@admin.register(FrontGameFavorite)
class FrontGameFavoriteAdmin(admin.ModelAdmin):
    """游戏收藏管理"""
    list_display = ['user', 'game', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'game__title']
    raw_id_fields = ['user', 'game']
    date_hierarchy = 'created_at'

@admin.register(FrontGameHistory)
class FrontGameHistoryAdmin(admin.ModelAdmin):
    """游戏历史管理"""
    list_display = ['user', 'game', 'play_count', 'last_played']
    list_filter = ['last_played']
    search_fields = ['user__username', 'game__title']
    raw_id_fields = ['user', 'game']
    date_hierarchy = 'last_played'

@admin.register(FrontGameComment)
class FrontGameCommentAdmin(admin.ModelAdmin):
    """游戏评论管理"""
    list_display = ['user', 'game', 'rating', 'likes', 'is_active', 'created_at']
    list_filter = ['rating', 'is_active', 'created_at']
    search_fields = ['user__username', 'game__title', 'content']
    raw_id_fields = ['user', 'game']
    date_hierarchy = 'created_at'
    actions = ['activate_comments', 'deactivate_comments']
    
    def activate_comments(self, request, queryset):
        """激活评论"""
        queryset.update(is_active=True)
    activate_comments.short_description = _("激活选中的评论")
    
    def deactivate_comments(self, request, queryset):
        """停用评论"""
        queryset.update(is_active=False)
    deactivate_comments.short_description = _("停用选中的评论")
