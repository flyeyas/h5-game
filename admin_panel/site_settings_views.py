from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.cache import cache

from .site_settings import SiteSettings
from .site_settings_forms import SiteSettingsForm
from .admin_site import custom_staff_member_required
from .models import AdminLog

@custom_staff_member_required
@permission_required('admin_panel.setting_view', raise_exception=True)
def site_settings_view(request):
    """网站设置查看页面"""
    # 获取或创建网站设置
    settings = SiteSettings.get_settings()
    
    # 处理非Ajax表单提交 (传统方式，保留向后兼容性)
    if request.method == 'POST' and request.user.has_perm('admin_panel.setting_edit') and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            
            # 记录操作日志
            AdminLog.objects.create(
                admin=request.user,
                action=_('更新了网站设置'),
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, _('网站设置已成功更新'))
            return redirect('admin_panel:site_settings')
    else:
        form = SiteSettingsForm(instance=settings)
    
    context = {
        'title': _('网站基本设置'),
        'form': form,
        'settings': settings
    }
    
    return render(request, 'admin/site_settings.html', context)

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
@require_http_methods(["POST"])
def ajax_update_site_settings(request):
    """通过Ajax更新网站设置"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': _('非法请求')}, status=400)
    
    # 获取现有设置
    settings = SiteSettings.get_settings()
    
    # 使用表单验证数据
    form = SiteSettingsForm(request.POST, request.FILES, instance=settings)
    
    if form.is_valid():
        # 保存表单
        settings = form.save()
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=_('通过Ajax更新了网站设置'),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # 构建响应数据 - 仅包含保留的字段
        response_data = {
            'status': 'success',
            'message': _('网站设置已成功更新'),
            'settings': {
                'site_name': settings.site_name,
                'site_description': settings.site_description,
                'site_keywords': settings.site_keywords,
            }
        }
        
        # 如果上传了新文件，返回文件URL
        if settings.site_logo:
            response_data['settings']['site_logo_url'] = settings.site_logo.url
        
        if settings.site_favicon:
            response_data['settings']['site_favicon_url'] = settings.site_favicon.url
            
        return JsonResponse(response_data)
    else:
        # 返回表单错误
        errors = {}
        for field in form.errors:
            errors[field] = form.errors[field][0]
        
        return JsonResponse({
            'status': 'error',
            'message': _('表单验证失败'),
            'errors': errors
        }, status=400)

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
@require_http_methods(["POST"])
def clear_site_settings_cache(request):
    """清除网站设置缓存"""
    cache.delete('site_settings')
    return JsonResponse({'status': 'success', 'message': _('网站设置缓存已清除')}) 