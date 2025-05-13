from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.conf import settings
import json

from .models import AdminLog
from .forms import MenuForm
from .menu import Menu

# 菜单管理列表
@login_required
def menu_list(request):
    """
    菜单管理列表页面
    """
    # 获取所有菜单
    menus = Menu.objects.all().order_by('order', 'id')
    
    # 只获取主菜单（用于表单中的父级菜单选项）
    main_menus = Menu.objects.filter(parent__isnull=True).order_by('order', 'name')
    
    context = {
        'menus': menus,
        'main_menus': main_menus,
        'title': _('后台导航菜单管理'),
    }
    
    return render(request, 'admin/menu_list.html', context)

# 添加菜单
@login_required
def add_menu(request):
    """
    添加菜单页面
    """
    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            menu = form.save()
            
            # 记录操作日志
            AdminLog.objects.create(
                admin=request.user,
                action=f'添加了菜单: {menu.name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # 如果是AJAX请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': _('菜单添加成功'),
                    'menu': {
                        'id': menu.id,
                        'name': menu.name,
                        'url': menu.url,
                        'icon': menu.icon,
                        'parent': menu.parent.id if menu.parent else None,
                        'order': menu.order,
                        'is_active': menu.is_active
                    }
                })
            
            messages.success(request, _('菜单添加成功'))
            return redirect('admin_panel:menu_list')
        else:
            # 如果是AJAX请求，返回表单错误信息
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': _('表单验证失败'),
                    'errors': {field: [error for error in errors] for field, errors in form.errors.items()}
                })
    else:
        form = MenuForm()
    
    return render(request, 'admin/menu_form.html', {
        'form': form,
        'title': _('添加菜单'),
        'is_add': True
    })

# 编辑菜单
@login_required
def edit_menu(request, menu_id):
    """
    编辑菜单页面
    """
    menu = get_object_or_404(Menu, id=menu_id)
    
    if request.method == 'POST':
        form = MenuForm(request.POST, instance=menu)
        if form.is_valid():
            menu = form.save()
            
            # 记录操作日志
            AdminLog.objects.create(
                admin=request.user,
                action=f'编辑了菜单: {menu.name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # 如果是AJAX请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': _('菜单修改成功'),
                    'menu': {
                        'id': menu.id,
                        'name': menu.name,
                        'url': menu.url,
                        'icon': menu.icon,
                        'parent': menu.parent.id if menu.parent else None,
                        'order': menu.order,
                        'is_active': menu.is_active
                    }
                })
            
            messages.success(request, _('菜单信息更新成功'))
            return redirect('admin_panel:menu_list')
        else:
            # 如果是AJAX请求，返回表单错误信息
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': _('表单验证失败'),
                    'errors': {field: [error for error in errors] for field, errors in form.errors.items()}
                })
    else:
        form = MenuForm(instance=menu)
    
    return render(request, 'admin/menu_form.html', {
        'form': form,
        'title': _('编辑菜单'),
        'is_add': False
    })

# 删除菜单
@login_required
def delete_menu(request, menu_id):
    """
    删除菜单
    """
    menu = get_object_or_404(Menu, id=menu_id)
    
    # 检查是否有子菜单
    if menu.children.exists():
        return JsonResponse({
            'status': 'error',
            'message': _('无法删除此菜单，请先删除其下的子菜单')
        })
    
    # 记录菜单名称，用于日志记录
    menu_name = menu.name
    
    # 删除菜单
    menu.delete()
    
    # 记录操作日志
    AdminLog.objects.create(
        admin=request.user,
        action=f'删除了菜单: {menu_name}',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'status': 'success',
        'message': _('菜单已删除')
    })

# 切换菜单状态
@login_required
def toggle_menu_status(request, menu_id):
    """
    切换菜单启用/禁用状态
    """
    menu = get_object_or_404(Menu, id=menu_id)
    
    # 切换状态
    menu.is_active = not menu.is_active
    menu.save()
    
    # 状态文本
    status_text = '启用' if menu.is_active else '禁用'
    
    # 记录操作日志
    AdminLog.objects.create(
        admin=request.user,
        action=f'{status_text}了菜单: {menu.name}',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({
        'status': 'success',
        'message': _(f'菜单已{status_text}'),
        'is_active': menu.is_active
    })

# 获取菜单项详细信息的API
@login_required
def get_menu_detail(request, menu_id):
    """
    获取菜单项详细信息的API
    """
    try:
        menu = Menu.objects.get(id=menu_id)
        
        # 返回菜单信息
        response_data = {
            'status': 'success',
            'menu': {
                'id': menu.id,
                'name': menu.name,
                'url': menu.url,
                'icon': menu.icon,
                'parent': menu.parent.id if menu.parent else None,
                'order': menu.order,
                'is_active': menu.is_active
            }
        }
        return JsonResponse(response_data)
    except Menu.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': _('菜单项不存在')
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': _('获取菜单数据时发生错误')
        })

# 保存菜单排序
@login_required
def save_menu_order(request):
    """
    保存菜单排序的API
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': _('无效的请求方法')
        })
    
    try:
        # 解析请求数据
        data = json.loads(request.body)
        menus = data.get('menus', [])
        
        # 更新菜单排序
        for menu_data in menus:
            menu_id = menu_data.get('id')
            new_order = menu_data.get('order')
            parent_id = menu_data.get('parent')
            
            menu = Menu.objects.get(id=menu_id)
            menu.order = new_order
            
            # 如果有父级菜单，则设置父级菜单
            if parent_id:
                menu.parent_id = parent_id
            else:
                menu.parent = None
            
            menu.save()
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=f'更新了菜单排序',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'status': 'success',
            'message': _('菜单排序已保存')
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

# 后台菜单管理
@login_required
def backend_menu_management(request):
    """
    后台菜单管理页面
    """
    # 获取所有菜单
    menus = Menu.objects.all().order_by('order', 'id')
    
    # 只获取主菜单（用于表单中的父级菜单选项）
    main_menus = Menu.objects.filter(parent__isnull=True).order_by('order', 'name')
    
    context = {
        'menus': menus,
        'main_menus': main_menus,
        'title': _('后台导航菜单管理'),
    }
    
    return render(request, 'admin/backend_menu_management.html', context)