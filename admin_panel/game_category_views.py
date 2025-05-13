import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.urls import reverse

from .game_category import GameCategory
logger = logging.getLogger(__name__)

@login_required
def game_category_list(request):
    """游戏分类列表页面"""
    # 获取搜索参数
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # 获取分页参数
    page_num = request.GET.get('page', 1)
    try:
        page_num = int(page_num)
        if page_num < 1:
            page_num = 1
    except ValueError:
        page_num = 1
    
    page_size = request.GET.get('page_size', 10)
    try:
        page_size = int(page_size)
        if page_size < 1:
            page_size = 10
    except ValueError:
        page_size = 10
    
    # 获取排序方式
    order_by = request.GET.get('order_by', 'order')
    if order_by not in ['name', 'order', 'game_count', '-name', '-order', '-game_count']:
        order_by = 'order'
    
    # 构建查询过滤条件
    filters = {}
    
    # 应用状态过滤
    if status_filter:
        is_active = status_filter == 'active'
        filters['is_active'] = is_active
    
    # 构建搜索过滤条件
    search_filters = None
    if search_query:
        search_filters = (
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(slug__icontains=search_query)
        )
    
    # 计算总数量（用于统计信息）
    total_count = GameCategory.objects.count()
    active_count = GameCategory.objects.filter(is_active=True).count()
    inactive_count = total_count - active_count
    
    # 构建查询 - 仅查询当前页需要的数据
    offset = (page_num - 1) * page_size
    limit = page_size
    
    # 执行查询 - 使用切片操作进行数据库层面的分页
    if search_filters:
        if filters:
            categories_query = GameCategory.objects.filter(search_filters, **filters)
        else:
            categories_query = GameCategory.objects.filter(search_filters)
    else:
        if filters:
            categories_query = GameCategory.objects.filter(**filters)
        else:
            categories_query = GameCategory.objects.all()
    
    # 获取当前查询条件下的总记录数
    filtered_count = categories_query.count()
    
    # 应用排序并获取分页数据
    categories = categories_query.order_by(order_by)[offset:offset+limit]
    logger.info(f"categories: {categories}")
    # 创建自定义分页对象
    total_pages = (filtered_count + page_size - 1) // page_size
    has_next = page_num < total_pages
    has_previous = page_num > 1
    
    # 获取父级分类选项（用于添加/编辑表单）
    parent_categories = GameCategory.objects.filter(parent__isnull=True)
    
    context = {
        'categories': categories,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'filtered_count': filtered_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'order_by': order_by,
        'parent_categories': parent_categories,
        'section': 'game_categories',
        'title': _('游戏分类管理'),
        'page': {
            'number': page_num,
            'has_previous': has_previous,
            'has_next': has_next,
            'previous_page_number': page_num - 1 if has_previous else None,
            'next_page_number': page_num + 1 if has_next else None,
            'total_pages': total_pages,
            'start_index': offset + 1 if filtered_count > 0 else 0,
            'end_index': min(offset + page_size, filtered_count),
            'total_items': filtered_count,
            'page_size': page_size,
        }
    }
    
    return render(request, 'admin/game_categories.html', context)


@login_required
@require_POST
def game_category_create(request):
    """创建游戏分类"""
    # 获取表单数据
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    parent_id = request.POST.get('parent', None)
    order = request.POST.get('order', 0)
    slug = request.POST.get('slug', '').strip()
    color = request.POST.get('color', '#6EBD6E')
    is_active = request.POST.get('is_active') == 'true'
    
    # 表单验证
    if not name:
        return JsonResponse({'status': 'error', 'message': _('分类名称不能为空')}, status=400)
    
    # 检查分类名称是否已存在
    if GameCategory.objects.filter(name=name).exists():
        return JsonResponse({'status': 'error', 'message': _('分类名称已存在')}, status=400)
    
    # 处理父级分类
    parent = None
    if parent_id and parent_id != 'null':
        try:
            parent = GameCategory.objects.get(id=parent_id)
        except GameCategory.DoesNotExist:
            pass
    
    # 创建分类
    try:
        category = GameCategory.objects.create(
            name=name,
            description=description,
            parent=parent,
            order=order,
            slug=slug,
            icon=request.POST.get('icon', 'fas fa-gamepad'),
            color=color,
            is_active=is_active,
        )
        
        # 记录日志(如果需要)
        
        return JsonResponse({
            'status': 'success', 
            'message': _('分类创建成功'),
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent': category.parent.name if category.parent else '-',
                'order': category.order,
                'icon': category.icon,
                'game_count': category.game_count,
                'is_active': category.is_active,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def game_category_detail(request, category_id):
    """获取游戏分类详情"""
    try:
        category = GameCategory.objects.get(id=category_id)
        return JsonResponse({
            'status': 'success',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent_id': category.parent.id if category.parent else None,
                'order': category.order,
                'slug': category.slug,
                'icon': category.icon,
                'color': category.color,
                'is_active': category.is_active,
                'game_count': category.game_count
            }
        })
    except GameCategory.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': _('分类不存在')}, status=404)


@login_required
@require_POST
def game_category_update(request, category_id):
    """更新游戏分类"""
    category = get_object_or_404(GameCategory, id=category_id)
    
    # 获取表单数据
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    parent_id = request.POST.get('parent', None)
    order = request.POST.get('order', 0)
    slug = request.POST.get('slug', '').strip()
    color = request.POST.get('color', '#6EBD6E')
    is_active = request.POST.get('is_active') == 'true'
    
    # 表单验证
    if not name:
        return JsonResponse({'status': 'error', 'message': _('分类名称不能为空')}, status=400)
    
    # 检查分类名称是否已存在(排除当前分类)
    if GameCategory.objects.filter(name=name).exclude(id=category_id).exists():
        return JsonResponse({'status': 'error', 'message': _('分类名称已存在')}, status=400)
    
    # 处理父级分类
    parent = None
    if parent_id and parent_id != 'null':
        try:
            parent = GameCategory.objects.get(id=parent_id)
            # 防止将分类设为自己的子分类
            if parent.id == category.id:
                return JsonResponse({'status': 'error', 'message': _('不能将分类设为自己的子分类')}, status=400)
        except GameCategory.DoesNotExist:
            pass
    
    # 更新分类
    try:
        category.name = name
        category.description = description
        category.parent = parent
        category.order = order
        if slug:
            category.slug = slug
        category.icon = request.POST.get('icon', category.icon)
        category.color = color
        category.is_active = is_active
        category.save()
        
        # 记录日志(如果需要)
        
        return JsonResponse({
            'status': 'success', 
            'message': _('分类更新成功'),
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent': category.parent.name if category.parent else '-',
                'order': category.order,
                'icon': category.icon,
                'game_count': category.game_count,
                'is_active': category.is_active,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def game_category_delete(request, category_id):
    """删除游戏分类"""
    category = get_object_or_404(GameCategory, id=category_id)
    
    # 检查是否有子分类
    if GameCategory.objects.filter(parent=category).exists():
        return JsonResponse({
            'status': 'error', 
            'message': _('该分类下有子分类，无法删除')
        }, status=400)
    
    # 检查是否有关联的游戏
    if category.game_count > 0:
        return JsonResponse({
            'status': 'error', 
            'message': _('该分类下有关联的游戏，无法删除')
        }, status=400)
    
    try:
        category_name = category.name
        category.delete()
        
        # 记录日志(如果需要)
        
        return JsonResponse({
            'status': 'success', 
            'message': _('分类"{}"已成功删除').format(category_name)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def game_category_toggle_status(request, category_id):
    """切换游戏分类状态（启用/禁用）"""
    category = get_object_or_404(GameCategory, id=category_id)
    
    try:
        category.is_active = not category.is_active
        category.save()
        
        status_text = _('启用') if category.is_active else _('禁用')
        
        # 记录日志(如果需要)
        
        return JsonResponse({
            'status': 'success', 
            'message': _('分类已{}').format(status_text),
            'is_active': category.is_active
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500) 