from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.cache import cache
import json

from .models import ConfigSettings, AdminLog
from .admin_site import custom_staff_member_required

@custom_staff_member_required
@permission_required('admin_panel.setting_view', raise_exception=True)
def config_settings_view(request):
    """系统配置管理页面"""
    # 获取所有配置项
    config_settings = ConfigSettings.objects.all().order_by('key')
    
    # 处理表单提交
    if request.method == 'POST' and request.user.has_perm('admin_panel.setting_edit'):
        key = request.POST.get('key')
        value = request.POST.get('value')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        if key:
            # 查找或创建配置项
            config, created = ConfigSettings.objects.get_or_create(
                key=key,
                defaults={
                    'value': value,
                    'description': description,
                    'is_active': is_active
                }
            )
            
            if not created:
                # 更新现有配置
                config.value = value
                config.description = description
                config.is_active = is_active
                config.save()
            
            # 记录操作日志
            action = _('创建了系统配置') if created else _('更新了系统配置')
            AdminLog.objects.create(
                admin=request.user,
                action=f"{action}: {key}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, _('系统配置已成功保存'))
            return redirect('admin_panel:config_settings')
    
    # 初始化表单数据（用于新建）
    form_data = {
        'key': '',
        'value': '',
        'description': '',
        'is_active': True
    }
    
    context = {
        'title': _('系统配置管理'),
        'config_settings': config_settings,
        'form_data': form_data
    }
    
    return render(request, 'admin/config_settings.html', context)

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
def edit_config_setting(request, config_id):
    """编辑系统配置"""
    config = get_object_or_404(ConfigSettings, id=config_id)
    
    if request.method == 'POST':
        config.value = request.POST.get('value')
        config.description = request.POST.get('description')
        config.is_active = request.POST.get('is_active') == 'on'
        config.save()
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=f"更新了系统配置: {config.key}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, _('系统配置已成功更新'))
        return redirect('admin_panel:config_settings')
    
    context = {
        'title': _('编辑系统配置'),
        'config': config
    }
    
    return render(request, 'admin/edit_config_setting.html', context)

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
@require_http_methods(["POST"])
def delete_config_setting(request, config_id):
    """删除系统配置"""
    config = get_object_or_404(ConfigSettings, id=config_id)
    key = config.key
    config.delete()
    
    # 记录操作日志
    AdminLog.objects.create(
        admin=request.user,
        action=f"删除了系统配置: {key}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    messages.success(request, _('系统配置已成功删除'))
    return redirect('admin_panel:config_settings')

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
@require_http_methods(["POST"])
def clear_config_cache(request):
    """清除系统配置缓存"""
    # 获取所有配置项
    configs = ConfigSettings.objects.all()
    
    # 清除每个配置项的缓存
    for config in configs:
        cache_key = f'config__{config.key}'
        cache.delete(cache_key)
    
    return JsonResponse({'status': 'success', 'message': _('系统配置缓存已清除')}) 