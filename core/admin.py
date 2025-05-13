from django.contrib import admin
from .models import Game, GameCategory, GameTag, SubscriptionPlan, PaymentGateway, Subscription, PaymentTransaction

@admin.register(GameCategory)
class GameCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description', 'icon', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)
    
    def has_module_permission(self, request):
        # 只允许管理员访问此模型
        return request.user.is_staff

@admin.register(GameTag)
class GameTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'games_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def games_count(self, obj):
        return obj.games.count()
    games_count.short_description = '游戏数量'
    
    def has_module_permission(self, request):
        # 只允许管理员访问此模型
        return request.user.is_staff

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_categories', 'status', 'is_featured', 'play_count', 'created_at')
    list_filter = ('status', 'is_featured', 'categories')
    search_fields = ('title', 'description')
    readonly_fields = ('play_count', 'rating', 'created_at', 'updated_at')
    filter_horizontal = ('categories', 'tags',)
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'slug', 'description', 'thumbnail', 'categories', 'tags')
        }),
        ('游戏内容', {
            'fields': ('iframe_url', 'iframe_width', 'iframe_height')
        }),
        ('状态设置', {
            'fields': ('status', 'is_featured')
        }),
        ('SEO设置', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('统计信息', {
            'fields': ('play_count', 'rating', 'created_at', 'updated_at')
        }),
    )
    
    def get_categories(self, obj):
        """获取游戏分类，用于列表显示"""
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = '分类'
    
    def has_module_permission(self, request):
        # 只允许管理员访问此模型
        return request.user.is_staff

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'period', 'is_active', 'created_at')
    list_filter = ('period', 'is_active')
    search_fields = ('name', 'description')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'price', 'period', 'description', 'is_active')
        }),
        ('功能特性', {
            'fields': ('features',)
        }),
    )
    
    def has_module_permission(self, request):
        # 只允许管理员访问此模型
        return request.user.is_staff

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ('name', 'gateway_type', 'is_active', 'is_default', 'test_mode', 'display_order')
    list_filter = ('gateway_type', 'is_active', 'test_mode', 'is_default')
    search_fields = ('name',)
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'gateway_type', 'is_active', 'is_default', 'test_mode', 'display_order')
        }),
        ('配置信息', {
            'fields': ('config',)
        }),
        ('URL设置', {
            'fields': ('success_url', 'cancel_url')
        }),
    )
    
    def has_module_permission(self, request):
        # 只允许管理员访问此模型
        return request.user.is_staff

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'payment_gateway', 'auto_renew')
    list_filter = ('status', 'auto_renew', 'is_trial', 'payment_gateway')
    search_fields = ('user__username', 'user__email', 'gateway_subscription_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'plan', 'status', 'start_date', 'end_date')
        }),
        ('支付信息', {
            'fields': ('payment_gateway', 'gateway_subscription_id')
        }),
        ('设置', {
            'fields': ('auto_renew', 'is_trial')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_module_permission(self, request):
        # 只允许管理员访问此模型
        return request.user.is_staff

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'currency', 'status', 'gateway', 'created_at')
    list_filter = ('status', 'transaction_type', 'gateway', 'currency')
    search_fields = ('user__username', 'user__email', 'gateway_transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'gateway_response')
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'subscription', 'transaction_type', 'amount', 'currency', 'status')
        }),
        ('网关信息', {
            'fields': ('gateway', 'gateway_transaction_id', 'gateway_response')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_module_permission(self, request):
        # 只允许管理员访问此模型
        return request.user.is_staff
