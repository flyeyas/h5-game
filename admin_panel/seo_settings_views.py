from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.cache import cache

from .models import SeoSettings, AdminLog
from .seo_settings_forms import SeoSettingsForm
from .admin_site import custom_staff_member_required

@custom_staff_member_required
@permission_required('admin_panel.setting_view', raise_exception=True)
def seo_settings_view(request):
    """SEO设置查看页面"""
    # 获取或创建SEO设置
    settings = SeoSettings.get_settings()
    
    # 处理非Ajax表单提交
    if request.method == 'POST' and request.user.has_perm('admin_panel.setting_edit') and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = SeoSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            
            # 记录操作日志
            AdminLog.objects.create(
                admin=request.user,
                action=_('更新了SEO设置'),
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, _('SEO设置已成功更新'))
            return redirect('admin_panel:seo_settings')
    else:
        form = SeoSettingsForm(instance=settings)
    
    context = {
        'title': _('SEO设置'),
        'form': form,
        'settings': settings
    }
    
    return render(request, 'admin/seo_settings.html', context)

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
@require_http_methods(["POST"])
def ajax_update_seo_settings(request):
    """通过Ajax更新SEO设置"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': _('非法请求')}, status=400)
    
    # 获取现有设置
    settings = SeoSettings.get_settings()
    
    # 使用表单验证数据
    form = SeoSettingsForm(request.POST, instance=settings)
    
    if form.is_valid():
        # 保存表单
        settings = form.save()
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=_('通过Ajax更新了SEO设置'),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # 构建响应数据
        response_data = {
            'status': 'success',
            'message': _('SEO设置已成功更新'),
            'settings': {
                'title_format': settings.title_format,
                'description_format': settings.description_format,
                'enable_sitemap': settings.enable_sitemap,
                'enable_canonical': settings.enable_canonical,
                'url_trailing_slash': settings.url_trailing_slash,
                'category_url_pattern': settings.category_url_pattern,
                'game_url_pattern': settings.game_url_pattern,
                'tag_url_pattern': settings.tag_url_pattern,
                'use_date_in_url': settings.use_date_in_url,
            }
        }
            
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
def clear_seo_settings_cache(request):
    """清除SEO设置缓存"""
    cache.delete('seo_settings')
    return JsonResponse({'status': 'success', 'message': _('SEO设置缓存已清除')}) 