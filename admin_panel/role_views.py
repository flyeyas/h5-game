from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.db import transaction
from django.contrib import messages
import json
import logging
from django.utils.translation import gettext_lazy as _

from .admin_user import Role, Permission, AdminUser
from .admin_site import admin_site_required, log_admin_action
from .models import AdminLog

logger = logging.getLogger('admin')

def log_admin_action(user, action, action_type, target):
    """记录管理员操作"""
    # 合并action_type和target到action中
    action_text = f"{action} [{action_type}] {target}"
    AdminLog.objects.create(
        admin=user,
        action=action_text,
        ip_address='127.0.0.1'  # 实际项目中应该从request中获取
    )

def get_all_permissions_by_category():
    """获取按分类分组的所有权限"""
    categories = {}
    permissions = Permission.objects.all().order_by('category', 'name')
    
    for perm in permissions:
        category = perm.get_category_display()
        if category not in categories:
            categories[category] = []
        categories[category].append(perm)
    
    return categories

@login_required
@admin_site_required
def roles_list(request):
    """角色列表页面"""
    roles = Role.objects.all().order_by('name')
    
    # 分页
    paginator = Paginator(roles, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_roles': roles.count(),
    }
    
    return render(request, 'admin/roles/role_list.html', context)

@login_required
@admin_site_required
def add_role(request):
    """添加角色"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, '角色名称不能为空')
            return redirect('roles_list')
        
        # 检查角色名是否已存在
        if Role.objects.filter(name=name).exists():
            messages.error(request, f'角色名 "{name}" 已存在')
            return redirect('roles_list')
        
        try:
            with transaction.atomic():
                role = Role.objects.create(
                    name=name,
                    description=description,
                    is_active=is_active
                )
                
                # 记录操作日志
                log_admin_action(
                    request.user, 
                    f'创建了新角色: {role.name}', 
                    'create', 
                    f'Role(id={role.id})'
                )
                
                messages.success(request, f'角色 "{role.name}" 创建成功')
                return redirect('roles_list')
        except Exception as e:
            logger.error(f"创建角色失败: {str(e)}")
            messages.error(request, f'创建角色失败: {str(e)}')
            return redirect('roles_list')
    
    return render(request, 'admin/roles/add_role.html')

@login_required
@admin_site_required
def edit_role(request, role_id):
    """编辑角色"""
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, '角色名称不能为空')
            return redirect('edit_role', role_id=role.id)
        
        # 检查角色名是否已存在(排除当前角色)
        if Role.objects.exclude(id=role.id).filter(name=name).exists():
            messages.error(request, f'角色名 "{name}" 已存在')
            return redirect('edit_role', role_id=role.id)
        
        try:
            with transaction.atomic():
                # 记录原始值用于日志
                old_values = {
                    'name': role.name,
                    'description': role.description,
                    'is_active': role.is_active
                }
                
                # 更新角色信息
                role.name = name
                role.description = description
                role.is_active = is_active
                role.save()
                
                # 记录操作日志
                changes = []
                if old_values['name'] != role.name:
                    changes.append(f"名称: {old_values['name']} -> {role.name}")
                if old_values['description'] != role.description:
                    changes.append(f"描述已更新")
                if old_values['is_active'] != role.is_active:
                    changes.append(f"状态: {'启用' if old_values['is_active'] else '禁用'} -> {'启用' if role.is_active else '禁用'}")
                
                log_message = f'更新了角色 "{role.name}" 的信息: {", ".join(changes)}'
                log_admin_action(
                    request.user, 
                    log_message, 
                    'update', 
                    f'Role(id={role.id})'
                )
                
                messages.success(request, f'角色 "{role.name}" 更新成功')
                return redirect('roles_list')
        except Exception as e:
            logger.error(f"更新角色失败: {str(e)}")
            messages.error(request, f'更新角色失败: {str(e)}')
            return redirect('edit_role', role_id=role.id)
    
    context = {
        'role': role
    }
    
    return render(request, 'admin/roles/edit_role.html', context)

@login_required
@admin_site_required
@require_POST
def delete_role(request, role_id):
    """删除角色"""
    role = get_object_or_404(Role, id=role_id)
    
    try:
        # 检查角色是否已分配给用户
        if role.admin_users.exists():
            return JsonResponse({
                'status': 'error',
                'message': f'无法删除角色 "{role.name}"，因为该角色已分配给 {role.admin_users.count()} 个管理员用户'
            })
        
        role_name = role.name
        role.delete()
        
        # 记录操作日志
        log_admin_action(
            request.user, 
            f'删除了角色: {role_name}', 
            'delete', 
            f'Role(id={role_id})'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'角色 "{role_name}" 已成功删除'
        })
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'删除角色失败: {str(e)}'
        })

@login_required
@admin_site_required
def role_permissions(request, role_id):
    """角色权限管理页面"""
    role = get_object_or_404(Role, id=role_id)
    
    # 获取所有权限并按类别分组
    all_permissions = Permission.objects.all().order_by('category', 'name')
    
    # 获取当前角色已有的权限ID集合
    role_permission_ids = role.permissions.values_list('id', flat=True)
    
    # 按类别分组权限
    permission_by_category = {}
    for perm in all_permissions:
        category = perm.get_category_display()
        if category not in permission_by_category:
            permission_by_category[category] = []
        
        permission_by_category[category].append({
            'id': perm.id,
            'name': perm.name,
            'codename': perm.codename,
            'description': perm.description,
            'checked': perm.id in role_permission_ids
        })
    
    context = {
        'role': role,
        'permission_by_category': permission_by_category
    }
    
    return render(request, 'admin/roles/role_permissions.html', context)

@login_required
@admin_site_required
@require_POST
def save_role_permissions(request, role_id):
    """保存角色权限"""
    role = get_object_or_404(Role, id=role_id)
    
    try:
        # 获取提交的权限ID列表
        permission_ids = request.POST.getlist('permissions')
        
        # 获取原始权限ID列表用于日志记录
        old_permission_ids = set(role.permissions.values_list('id', flat=True))
        new_permission_ids = set(map(int, permission_ids))
        
        # 添加的权限
        added_permissions = new_permission_ids - old_permission_ids
        # 移除的权限
        removed_permissions = old_permission_ids - new_permission_ids
        
        with transaction.atomic():
            # 清空现有权限并设置新权限
            role.permissions.clear()
            if permission_ids:
                permissions = Permission.objects.filter(id__in=permission_ids)
                role.permissions.add(*permissions)
            
            # 记录日志
            if added_permissions or removed_permissions:
                changes = []
                
                if added_permissions:
                    added_perm_names = Permission.objects.filter(id__in=added_permissions).values_list('name', flat=True)
                    changes.append(f"添加权限: {', '.join(added_perm_names)}")
                
                if removed_permissions:
                    removed_perm_names = Permission.objects.filter(id__in=removed_permissions).values_list('name', flat=True)
                    changes.append(f"移除权限: {', '.join(removed_perm_names)}")
                
                log_message = f'更新了角色 "{role.name}" 的权限: {"; ".join(changes)}'
                log_admin_action(
                    request.user, 
                    log_message, 
                    'update', 
                    f'Role(id={role.id})'
                )
            
            messages.success(request, f'角色 "{role.name}" 的权限已更新')
            return redirect('admin_panel:roles_list')
    except Exception as e:
        logger.error(f"更新角色权限失败: {str(e)}")
        messages.error(request, f'更新角色权限失败: {str(e)}')
        return redirect('admin_panel:role_permissions', role_id=role.id)

@login_required
@admin_site_required
def user_roles_management(request, user_id):
    """用户角色管理页面"""
    # 检查权限
    if not request.user.has_permission('manage_roles'):
        messages.error(request, '您没有管理用户角色的权限')
        return redirect('admin_panel:dashboard')
    
    user = get_object_or_404(AdminUser, id=user_id)
    
    # 获取所有可用角色
    all_roles = Role.objects.all()
    
    # 获取用户当前角色
    user_roles = user.roles.all()
    
    # 获取所有权限分类
    all_permissions = get_all_permissions_by_category()
    
    # 获取用户自定义权限
    user_custom_permissions = user.custom_permissions.all()
    
    context = {
        'user': user,
        'roles': all_roles,
        'user_roles': [role.id for role in user_roles],
        'user_overrides': [perm.codename for perm in user_custom_permissions],
        'enable_custom_permissions': user.custom_permissions.exists(),
    }
    
    return render(request, 'admin/user_roles.html', context)

@login_required
@admin_site_required
@require_POST
def save_user_roles(request, user_id):
    """保存用户角色和自定义权限"""
    # 检查权限
    if not request.user.has_permission('manage_roles'):
        return JsonResponse({
            'status': 'error',
            'message': '您没有管理用户角色的权限'
        })
    
    try:
        with transaction.atomic():
            user = get_object_or_404(AdminUser, id=user_id)
            
            # 保存角色
            selected_role_ids = request.POST.getlist('roles')
            new_roles = Role.objects.filter(id__in=selected_role_ids)
            
            # 获取旧角色，用于记录变更
            old_roles = user.roles.all()
            old_role_names = [role.name for role in old_roles]
            new_role_names = [role.name for role in new_roles]
            
            # 清除并重新设置用户角色
            user.roles.clear()
            user.roles.add(*new_roles)
            
            # 保存自定义权限覆盖
            enable_custom_permissions = 'enable_custom_permissions' in request.POST
            custom_perms = request.POST.getlist('overrides') if enable_custom_permissions else []
            
            # 清除旧的自定义权限
            user.custom_permissions.clear()
            
            # 添加新的自定义权限
            if custom_perms:
                permissions = Permission.objects.filter(codename__in=custom_perms)
                user.custom_permissions.add(*permissions)
            
            # 记录变更信息
            changes = []
            
            # 计算添加的角色
            added_roles = [name for name in new_role_names if name not in old_role_names]
            if added_roles:
                changes.append(f"添加角色: {', '.join(added_roles)}")
            
            # 计算移除的角色
            removed_roles = [name for name in old_role_names if name not in new_role_names]
            if removed_roles:
                changes.append(f"移除角色: {', '.join(removed_roles)}")
            
            # 记录自定义权限变更
            if custom_perms:
                changes.append(f"设置了 {len(custom_perms)} 个自定义权限")
            
            # 记录日志
            if changes:
                log_message = f'更新了用户 "{user.username}" 的角色和权限: {"; ".join(changes)}'
                log_admin_action(
                    request.user, 
                    log_message, 
                    'update', 
                    f'AdminUser(id={user.id})'
                )
            
            # 返回成功的JSON响应
            return JsonResponse({
                'status': 'success',
                'message': f'用户 "{user.username}" 的角色和权限已更新',
                'changes': changes
            })
    except Exception as e:
        logger.error(f"更新用户角色和权限失败: {str(e)}")
        # 返回错误的JSON响应
        return JsonResponse({
            'status': 'error',
            'message': f'更新用户角色和权限失败: {str(e)}'
        }) 