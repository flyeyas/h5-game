from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from .admin_site import custom_staff_member_required
from .models import AdminLog

@custom_staff_member_required
@permission_required('socialaccount.view_socialapp', raise_exception=True)
def social_app_list_view(request):
    """社交应用列表视图"""
    social_apps = SocialApp.objects.all()
    
    context = {
        'title': _('社交应用管理'),
        'social_apps': social_apps,
    }
    
    return render(request, 'admin/social_apps/list.html', context)

@custom_staff_member_required
@permission_required('socialaccount.change_socialapp', raise_exception=True)
def social_app_edit_view(request, app_id):
    """编辑社交应用视图"""
    social_app = get_object_or_404(SocialApp, id=app_id)
    sites = Site.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        provider = request.POST.get('provider')
        client_id = request.POST.get('client_id')
        secret = request.POST.get('secret')
        key = request.POST.get('key', '')
        site_ids = request.POST.getlist('sites')
        
        # 验证必填字段
        if not name or not provider or not client_id or not secret:
            messages.error(request, _('请填写所有必填字段'))
            return redirect('admin_panel:social_app_edit', app_id=app_id)
        
        # 更新社交应用
        social_app.name = name
        social_app.provider = provider
        social_app.client_id = client_id
        social_app.secret = secret
        social_app.key = key
        social_app.save()
        
        # 更新关联站点
        social_app.sites.clear()
        for site_id in site_ids:
            site = Site.objects.get(id=site_id)
            social_app.sites.add(site)
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=_('更新了社交应用: {}').format(social_app.name),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, _('社交应用已成功更新'))
        return redirect('admin_panel:social_app_list')
    
    context = {
        'title': _('编辑社交应用'),
        'social_app': social_app,
        'sites': sites,
        'providers': [
            ('google', 'Google'),
            ('facebook', 'Facebook'),
            ('github', 'GitHub'),
            ('twitter', 'Twitter'),
        ]
    }
    
    return render(request, 'admin/social_apps/edit.html', context)

@custom_staff_member_required
@permission_required('socialaccount.add_socialapp', raise_exception=True)
def social_app_create_view(request):
    """创建社交应用视图"""
    sites = Site.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        provider = request.POST.get('provider')
        client_id = request.POST.get('client_id')
        secret = request.POST.get('secret')
        key = request.POST.get('key', '')
        site_ids = request.POST.getlist('sites')
        
        # 验证必填字段
        if not name or not provider or not client_id or not secret:
            messages.error(request, _('请填写所有必填字段'))
            return redirect('admin_panel:social_app_create')
        
        # 创建社交应用
        social_app = SocialApp.objects.create(
            name=name,
            provider=provider,
            client_id=client_id,
            secret=secret,
            key=key
        )
        
        # 添加关联站点
        for site_id in site_ids:
            site = Site.objects.get(id=site_id)
            social_app.sites.add(site)
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=_('创建了社交应用: {}').format(social_app.name),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, _('社交应用已成功创建'))
        return redirect('admin_panel:social_app_list')
    
    context = {
        'title': _('创建社交应用'),
        'sites': sites,
        'providers': [
            ('google', 'Google'),
            ('facebook', 'Facebook'),
            ('github', 'GitHub'),
            ('twitter', 'Twitter'),
        ]
    }
    
    return render(request, 'admin/social_apps/create.html', context)

@custom_staff_member_required
@permission_required('socialaccount.delete_socialapp', raise_exception=True)
def social_app_delete_view(request, app_id):
    """删除社交应用视图"""
    social_app = get_object_or_404(SocialApp, id=app_id)
    
    name = social_app.name
    social_app.delete()
    
    # 记录操作日志
    AdminLog.objects.create(
        admin=request.user,
        action=_('删除了社交应用: {}').format(name),
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    messages.success(request, _('社交应用已成功删除'))
    return redirect('admin_panel:social_app_list')

@custom_staff_member_required
@permission_required('socialaccount.view_socialapp', raise_exception=True)
def social_app_detail_view(request, app_id):
    """查看社交应用详情"""
    social_app = get_object_or_404(SocialApp, id=app_id)
    
    context = {
        'title': _('社交应用详情'),
        'social_app': social_app,
    }
    
    return render(request, 'admin/social_apps/detail.html', context) 