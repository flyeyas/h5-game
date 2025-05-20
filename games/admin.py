from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Game, Category, Advertisement, 
    UserProfile, Membership
)
from .models_menu_settings import Language, Menu, MenuItem, WebsiteSetting
from .models_payment import MembershipPlan, MembershipPayment, PaymentMethod, PaymentTemplate


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'categories', 'is_featured', 'is_active', 'created_at')
    list_filter = ('is_featured', 'is_active', 'categories')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    
    def categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    categories.short_description = _('分类')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'order')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'is_active', 'start_date', 'end_date')
    list_filter = ('position', 'is_active')
    search_fields = ('name', 'content')
    date_hierarchy = 'start_date'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'created_at'


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'price', 'duration_days', 'is_active')
    list_filter = ('level', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu_type', 'is_active')
    list_filter = ('menu_type', 'is_active')
    search_fields = ('name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'menu', 'parent', 'url', 'order', 'is_active')
    list_filter = ('menu', 'is_active')
    search_fields = ('title',)


@admin.register(WebsiteSetting)
class WebsiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name',)
    search_fields = ('site_name', 'site_description')


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'is_default')
    list_filter = ('is_active', 'is_default')
    search_fields = ('code', 'name')


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('membership', 'plan')


@admin.register(MembershipPayment)
class MembershipPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'membership', 'total', 'status', 'created_at')
    list_filter = ('status', 'membership', 'is_recurring')
    search_fields = ('user__username', 'user__email', 'transaction_id')
    date_hierarchy = 'created_at'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'provider_class')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'provider_class', 'is_active', 'sort_order')
        }),
        (_('Display Settings'), {
            'fields': ('icon', 'description')
        }),
        (_('Configuration'), {
            'fields': ('configuration',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentTemplate)
class PaymentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'template_type', 'status', 'created_at', 'updated_at')
    list_filter = ('template_type', 'status')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'template_type', 'status')
        }),
        (_('Template Content'), {
            'fields': ('subject', 'content', 'variables')
        }),
        (_('Additional Information'), {
            'fields': ('description',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )