from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib.sites.models import Site

from .admin_site import custom_staff_member_required
from .models import AdminLog

@custom_staff_member_required
@permission_required('sites.view_site', raise_exception=True)
def sites_list_view(request):
    """Sites 应用列表视图"""
    sites = Site.objects.all()
    
    context = {
        'title': _('站点管理'),
        'sites': sites,
    }
    
    return render(request, 'admin/sites/list.html', context)

@custom_staff_member_required
@permission_required('sites.change_site', raise_exception=True)
def site_edit_view(request, site_id):
    """编辑站点视图"""
    site = get_object_or_404(Site, id=site_id)
    
    if request.method == 'POST':
        domain = request.POST.get('domain')
        name = request.POST.get('name')
        
        if not domain:
            messages.error(request, _('域名不能为空'))
            return redirect('admin_panel:site_edit', site_id=site_id)
        
        site.domain = domain
        site.name = name
        site.save()
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=_('更新了站点: {}').format(site.domain),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, _('站点已成功更新'))
        return redirect('admin_panel:sites_list')
    
    context = {
        'title': _('编辑站点'),
        'site': site,
    }
    
    return render(request, 'admin/sites/edit.html', context)

@custom_staff_member_required
@permission_required('sites.add_site', raise_exception=True)
def site_create_view(request):
    """创建站点视图"""
    if request.method == 'POST':
        domain = request.POST.get('domain')
        name = request.POST.get('name')
        
        if not domain:
            messages.error(request, _('域名不能为空'))
            return redirect('admin_panel:site_create')
        
        site = Site.objects.create(domain=domain, name=name)
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=_('创建了新站点: {}').format(site.domain),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, _('站点已成功创建'))
        return redirect('admin_panel:sites_list')
    
    context = {
        'title': _('创建站点'),
    }
    
    return render(request, 'admin/sites/create.html', context)

@custom_staff_member_required
@permission_required('sites.delete_site', raise_exception=True)
def site_delete_view(request, site_id):
    """删除站点视图"""
    site = get_object_or_404(Site, id=site_id)
    
    # 检查是否是默认站点（ID为1）
    if site.id == 1:
        messages.error(request, _('默认站点不能删除'))
        return redirect('admin_panel:sites_list')
    
    domain = site.domain
    site.delete()
    
    # 记录操作日志
    AdminLog.objects.create(
        admin=request.user,
        action=_('删除了站点: {}').format(domain),
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    messages.success(request, _('站点已成功删除'))
    return redirect('admin_panel:sites_list')

@custom_staff_member_required
@permission_required('sites.change_site', raise_exception=True)
@require_http_methods(["POST"])
def ajax_update_site(request, site_id):
    """通过Ajax更新站点"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': _('非法请求')}, status=400)
    
    site = get_object_or_404(Site, id=site_id)
    
    domain = request.POST.get('domain')
    name = request.POST.get('name')
    
    if not domain:
        return JsonResponse({
            'status': 'error',
            'message': _('域名不能为空'),
        }, status=400)
    
    site.domain = domain
    site.name = name
    site.save()
    
    # 记录操作日志
    AdminLog.objects.create(
        admin=request.user,
        action=_('通过Ajax更新了站点: {}').format(site.domain),
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'status': 'success',
        'message': _('站点已成功更新'),
        'site': {
            'id': site.id,
            'domain': site.domain,
            'name': site.name,
        }
    }) 