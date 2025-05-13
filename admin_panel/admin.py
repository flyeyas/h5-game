from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission, Group, User
from django.utils.html import format_html
import json

from .models import AdminLog, SeoSettings, ConfigSettings
# from .admin_user import AdminUser
from .admin_user import AdminProfile
from .admin_site import CustomAdminSite
from .menu import Menu

# 替换默认的AdminSite
admin.site = CustomAdminSite(name='admin')
admin.site.site_header = _('GameHub管理系统')
admin.site.site_title = _('GameHub管理后台')
admin.site.index_title = _('管理首页')

# 注册权限和用户组
admin.site.register(Permission)
admin.site.register(Group)

# 注册ConfigSettings模型
admin.site.register(ConfigSettings)

# 注册管理员资料模型
@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'real_name', 'role', 'status', 'get_email', 'last_login_time')
    list_filter = ('role', 'status')
    search_fields = ('user__username', 'real_name', 'user__email', 'mobile')
    readonly_fields = ('created_time',)
    fieldsets = (
        (_('用户关联'), {'fields': ('user',)}),
        (_('基本信息'), {'fields': ('real_name', 'avatar', 'mobile')}),
        (_('角色权限'), {'fields': ('role', 'status', 'custom_permissions')}),
        (_('时间信息'), {'fields': ('last_login_time', 'created_time')}),
        (_('其他信息'), {'fields': ('notes',)}),
    )
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = _('邮箱')
    
    def save_model(self, request, obj, form, change):
        """重写保存方法，处理权限"""
        # 保存用户资料
        super().save_model(request, obj, form, change)
        
        # 记录操作日志
        action = '修改' if change else '创建'
        AdminLog.objects.create(
            admin=request.user,
            action=f'{action}了管理员资料: {obj.user.username}',
            ip_address=request.META.get('REMOTE_ADDR')
        )

# 注册SEO设置
@admin.register(SeoSettings)
class SeoSettingsAdmin(admin.ModelAdmin):
    """SEO设置管理员类"""
    list_display = ('page_type', 'title_template')
    list_filter = ('page_type',)
    search_fields = ('page_type', 'title_template', 'description_template')
    fieldsets = (
        (_('基本设置'), {
            'fields': ('page_type', 'title_template', 'description_template', 'keywords')
        }),
        (_('Open Graph设置'), {
            'fields': ('og_title_template', 'og_description_template', 'og_image'),
            'classes': ('collapse',)
        }),
    )

# 注册配置设置
@admin.register(ConfigSettings)
class ConfigSettingsAdmin(admin.ModelAdmin):
    """配置设置管理员类"""
    list_display = ('key', 'description', 'formatted_value')
    list_filter = ('is_active',)
    search_fields = ('key', 'description')
    fieldsets = (
        (None, {
            'fields': ('key', 'description', 'value', 'is_active')
        }),
        (_('格式化值'), {
            'fields': ('formatted_value',),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_value(self, obj):
        """格式化JSON值显示"""
        try:
            # 尝试解析JSON字符串
            value_dict = json.loads(obj.value) if isinstance(obj.value, str) else obj.value
            
            # 格式化为美观的JSON
            formatted_json = json.dumps(value_dict, indent=2, ensure_ascii=False)
            
            # 返回预格式化的HTML
            return format_html('<pre>{}</pre>', formatted_json)
        except Exception:
            return obj.value
    
    formatted_value.short_description = _('格式化值')

# 注册操作日志
@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    """操作日志管理员类"""
    list_display = ('admin', 'action', 'ip_address', 'created_at')
    list_filter = ('admin', 'created_at')
    search_fields = ('admin__username', 'action', 'ip_address')
    readonly_fields = ('admin', 'action', 'ip_address', 'created_at')
    
    def has_add_permission(self, request):
        # 禁止手动添加日志
        return False
    
    def has_change_permission(self, request, obj=None):
        # 禁止修改日志
        return False

# 注册菜单模型
@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'parent', 'order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'url')
    list_editable = ('order', 'is_active')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 记录操作日志
        action = '修改' if change else '创建'
        AdminLog.objects.create(
            admin=request.user,
            action=f'{action}了菜单: {obj.name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )