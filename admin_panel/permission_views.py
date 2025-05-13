from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
from django.contrib import messages
import logging

from .admin_user import Permission
from .admin_site import admin_site_required, log_admin_action

logger = logging.getLogger('admin')

@login_required
@admin_site_required
def permissions_list(request):
    """权限列表页面"""
    # 获取所有权限并分页
    permissions = Permission.objects.all().order_by('category', 'name')
    
    # 支持按分类和关键词筛选
    category = request.GET.get('category')
    keyword = request.GET.get('keyword')
    
    if category:
        permissions = permissions.filter(category=category)
    if keyword:
        permissions = permissions.filter(name__icontains=keyword) | permissions.filter(codename__icontains=keyword)
    
    # 分页
    paginator = Paginator(permissions, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取所有可用的权限类别
    categories = list(set(Permission.objects.values_list('category', flat=True)))
    categories.sort()
    
    context = {
        'page_obj': page_obj,
        'total_permissions': permissions.count(),
        'categories': categories,
        'category': category,
        'keyword': keyword,
    }
    
    return render(request, 'admin/permissions/permission_list.html', context)

@login_required
@admin_site_required
def add_permission(request):
    """添加权限"""
    if request.method == 'POST':
        name = request.POST.get('name')
        codename = request.POST.get('codename')
        category = request.POST.get('category')
        description = request.POST.get('description')
        
        if not name or not codename or not category:
            messages.error(request, '权限名称、代码名和分类不能为空')
            return redirect('add_permission')
        
        # 检查代码名是否已存在
        if Permission.objects.filter(codename=codename).exists():
            messages.error(request, f'权限代码名 "{codename}" 已存在')
            return redirect('add_permission')
        
        try:
            with transaction.atomic():
                permission = Permission.objects.create(
                    name=name,
                    codename=codename,
                    category=category,
                    description=description
                )
                
                # 记录操作日志
                log_admin_action(
                    request.user, 
                    f'创建了新权限: {permission.name} ({permission.codename})', 
                    'create', 
                    f'Permission(id={permission.id})'
                )
                
                messages.success(request, f'权限 "{permission.name}" 创建成功')
                return redirect('permissions_list')
        except Exception as e:
            logger.error(f"创建权限失败: {str(e)}")
            messages.error(request, f'创建权限失败: {str(e)}')
            return redirect('add_permission')
    
    # 获取所有可用的权限类别
    categories = list(set(Permission.objects.values_list('category', flat=True)))
    categories.sort()
    
    context = {
        'categories': categories
    }
    
    return render(request, 'admin/permissions/add_permission.html', context)

@login_required
@admin_site_required
def edit_permission(request, permission_id):
    """编辑权限"""
    permission = get_object_or_404(Permission, id=permission_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        codename = request.POST.get('codename')
        category = request.POST.get('category')
        description = request.POST.get('description')
        
        if not name or not codename or not category:
            messages.error(request, '权限名称、代码名和分类不能为空')
            return redirect('edit_permission', permission_id=permission.id)
        
        # 检查代码名是否已存在(排除当前权限)
        if Permission.objects.exclude(id=permission.id).filter(codename=codename).exists():
            messages.error(request, f'权限代码名 "{codename}" 已存在')
            return redirect('edit_permission', permission_id=permission.id)
        
        try:
            with transaction.atomic():
                # 记录原始值用于日志
                old_values = {
                    'name': permission.name,
                    'codename': permission.codename,
                    'category': permission.category,
                    'description': permission.description
                }
                
                # 更新权限信息
                permission.name = name
                permission.codename = codename
                permission.category = category
                permission.description = description
                permission.save()
                
                # 记录操作日志
                changes = []
                if old_values['name'] != permission.name:
                    changes.append(f"名称: {old_values['name']} -> {permission.name}")
                if old_values['codename'] != permission.codename:
                    changes.append(f"代码名: {old_values['codename']} -> {permission.codename}")
                if old_values['category'] != permission.category:
                    changes.append(f"分类: {old_values['category']} -> {permission.category}")
                if old_values['description'] != permission.description:
                    changes.append(f"描述已更新")
                
                log_message = f'更新了权限 "{permission.name}" 的信息: {", ".join(changes)}'
                log_admin_action(
                    request.user, 
                    log_message, 
                    'update', 
                    f'Permission(id={permission.id})'
                )
                
                messages.success(request, f'权限 "{permission.name}" 更新成功')
                return redirect('permissions_list')
        except Exception as e:
            logger.error(f"更新权限失败: {str(e)}")
            messages.error(request, f'更新权限失败: {str(e)}')
            return redirect('edit_permission', permission_id=permission.id)
    
    # 获取所有可用的权限类别
    categories = list(set(Permission.objects.values_list('category', flat=True)))
    categories.sort()
    
    context = {
        'permission': permission,
        'categories': categories
    }
    
    return render(request, 'admin/permissions/edit_permission.html', context)

@login_required
@admin_site_required
@require_POST
def delete_permission(request, permission_id):
    """删除权限"""
    permission = get_object_or_404(Permission, id=permission_id)
    
    try:
        # 检查权限是否已分配给角色
        if permission.roles.exists():
            return JsonResponse({
                'status': 'error',
                'message': f'无法删除权限 "{permission.name}"，因为该权限已分配给 {permission.roles.count()} 个角色'
            })
        
        # 检查权限是否已直接分配给用户
        if permission.admin_users.exists():
            return JsonResponse({
                'status': 'error',
                'message': f'无法删除权限 "{permission.name}"，因为该权限已直接分配给 {permission.admin_users.count()} 个用户'
            })
        
        permission_name = permission.name
        permission.delete()
        
        # 记录操作日志
        log_admin_action(
            request.user, 
            f'删除了权限: {permission_name} ({permission.codename})', 
            'delete', 
            f'Permission(id={permission_id})'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'权限 "{permission_name}" 已成功删除'
        })
    except Exception as e:
        logger.error(f"删除权限失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'删除权限失败: {str(e)}'
        }) 