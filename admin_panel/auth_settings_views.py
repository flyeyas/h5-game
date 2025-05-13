from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
import json
from django.urls import reverse

from .models import ConfigSettings, AdminLog
from .admin_site import custom_staff_member_required

@custom_staff_member_required
def auth_settings_view(request):
    """认证设置页面"""
    # 获取当前设置
    enable_login = ConfigSettings.get_config('enable_login', True)
    enable_register = ConfigSettings.get_config('enable_register', True)
    enable_comments = ConfigSettings.get_config('enable_comments', True)
    show_member_content = ConfigSettings.get_config('show_member_content', True)
    
    # 如果配置值是字符串，则转换为布尔值
    if isinstance(enable_login, str):
        enable_login = enable_login.lower() not in ('false', '0')
    if isinstance(enable_register, str):
        enable_register = enable_register.lower() not in ('false', '0')
    if isinstance(enable_comments, str):
        enable_comments = enable_comments.lower() not in ('false', '0')
    if isinstance(show_member_content, str):
        show_member_content = show_member_content.lower() not in ('false', '0')
    
    # 处理提交
    if request.method == 'POST' and request.user.has_perm('admin_panel.setting_edit'):
        enable_login = request.POST.get('enable_login') == 'on'
        enable_register = request.POST.get('enable_register') == 'on'
        enable_comments = request.POST.get('enable_comments') == 'on'
        show_member_content = request.POST.get('show_member_content') == 'on'
        
        # 保存设置
        login_config = ConfigSettings.objects.update_or_create(
            key='enable_login',
            defaults={'value': json.dumps(enable_login), 'description': '开启前台登录功能', 'is_active': True}
        )[0]
        
        register_config = ConfigSettings.objects.update_or_create(
            key='enable_register',
            defaults={'value': json.dumps(enable_register), 'description': '开启前台注册功能', 'is_active': True}
        )[0]
        
        comments_config = ConfigSettings.objects.update_or_create(
            key='enable_comments',
            defaults={'value': json.dumps(enable_comments), 'description': '开启前台评论功能', 'is_active': True}
        )[0]
        
        member_config = ConfigSettings.objects.update_or_create(
            key='show_member_content',
            defaults={'value': json.dumps(show_member_content), 'description': '显示会员相关内容', 'is_active': True}
        )[0]
        
        # 记录操作日志
        changes = {
            'enable_login': enable_login,
            'enable_register': enable_register,
            'enable_comments': enable_comments,
            'show_member_content': show_member_content
        }
        
        # 添加日志
        AdminLog.objects.create(
            admin=request.user,
            action=f'更新认证设置: 登录={enable_login}, 注册={enable_register}, 评论={enable_comments}, 会员内容={show_member_content}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # 清除缓存
        cache.delete('config__enable_login')
        cache.delete('config__enable_register')
        cache.delete('config__enable_comments')
        cache.delete('config__show_member_content')
        
        messages.success(request, _('认证设置已更新'))
        return redirect('admin_panel:auth_settings')
    
    # 渲染页面
    context = {
        'enable_login': enable_login,
        'enable_register': enable_register,
        'enable_comments': enable_comments,
        'show_member_content': show_member_content,
        'title': _('认证与功能设置'),
        'module': 'settings',
        'section': 'auth_settings',
        'admin_panel_namespace': 'admin_panel'  # 添加命名空间信息到上下文
    }
    
    return render(request, 'admin/auth_settings.html', context) 