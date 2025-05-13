import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.utils.text import slugify
import hashlib
import time
from math import ceil
from django.db import connection

from .game import GameTag

logger = logging.getLogger(__name__)
@login_required
def tag_list(request):
    """标签列表页面"""
    # 记录请求参数和开始时间
    start_time = time.time()
    logger.info(f"处理标签列表请求: {request.GET}")
    
    # 启用SQL查询记录
    from django.db import reset_queries
    reset_queries()
    
    # 获取搜索参数
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # 查询标签基础查询集 - 添加游戏计数注解
    # 使用only限制查询字段，减少数据传输量
    # 使用select_related减少查询次数
    tags_query = GameTag.objects.all().only(
        'id', 'name', 'slug', 'is_active', 'created_at', 'updated_at'
    ).annotate(games_count=Count('games'))
    logger.info(f"初始查询: {str(tags_query.query)}")
    # 添加查询提示(hint)以使用索引，提高查询效率
    if status_filter or search_query:
        # 为搜索和过滤场景添加查询提示
        tags_query = tags_query.extra(
            select={'_hint': "/*+ INDEX(core_gametag core_gametag_name_idx) */"}
        )
    
    logger.info(f"初始查询: {str(tags_query.query)}")
    
    # 应用搜索过滤
    if search_query:
        tags_query = tags_query.filter(name__icontains=search_query)
        logger.info(f"添加搜索过滤后查询: {str(tags_query.query)}")
    
    # 应用状态过滤
    if status_filter:
        if status_filter == 'active':
            tags_query = tags_query.filter(is_active=True)
        elif status_filter == 'inactive':
            tags_query = tags_query.filter(is_active=False)
        logger.info(f"添加状态过滤后查询: {str(tags_query.query)}")
    
    # 获取排序参数
    order_by = request.GET.get('order_by', 'id')
    valid_order_fields = ['id', '-id', 'name', '-name', 'is_active', '-is_active', 
                          'games_count', '-games_count', 'created_at', '-created_at']
    
    # 处理排序，同时兼容旧的game_count参数
    if order_by:
        # 处理游戏数量排序的情况
        if order_by == 'game_count':
            order_by = 'games_count'
        elif order_by == '-game_count':
            order_by = '-games_count'
        
        # 检查是否为有效排序字段
        if order_by in valid_order_fields:
            tags_query = tags_query.order_by(order_by)
            logger.info(f"使用排序: {order_by}")
        else:
            # 如果是无效字段，使用默认排序
            tags_query = tags_query.order_by('id')
            logger.info(f"无效排序字段 '{order_by}'，使用默认排序: id")
    else:
        # 默认排序
        tags_query = tags_query.order_by('id')
        logger.info("未指定排序，使用默认排序: id")
    
    # 为提高性能，单独计算总数，仅选择需要的字段
    count_query = tags_query.values('id')
    total_count = count_query.count()
    
    # 统计活跃和非活跃标签数量 - 使用聚合查询减少数据库请求
    from django.db.models import Case, When, Value, IntegerField, Sum
    status_stats = GameTag.objects.aggregate(
        active_count=Sum(Case(
            When(is_active=True, then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )),
        inactive_count=Sum(Case(
            When(is_active=False, then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        ))
    )
    active_count = status_stats['active_count'] or 0
    inactive_count = status_stats['inactive_count'] or 0
    
    logger.info(f"记录总数: {total_count}, 活跃: {active_count}, 非活跃: {inactive_count}")
    
    # 数据库层面的分页
    page_size = 10  # 每页显示的记录数
    try:
        page = int(request.GET.get('page', 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    offset = (page - 1) * page_size
    
    # 使用offset和limit进行数据库层面的分页
    # 添加SQL_CALC_FOUND_ROWS提示以优化COUNT查询
    query_hint = "/*+ SQL_CALC_FOUND_ROWS */"
    tags = list(tags_query[offset:offset + page_size])  # 强制执行查询并转为列表
    
    # 记录查询执行时间
    query_time = time.time() - start_time
    logger.info(f"查询耗时: {query_time:.4f}秒")
    
    # 记录实际执行的分页SQL
    if connection.queries:
        for i, query in enumerate(connection.queries):
            logger.info(f"SQL查询 #{i+1}: {query['sql']}")
            logger.info(f"SQL耗时: {float(query['time']):.4f}秒")
    else:
        logger.warning("无法获取执行的SQL查询，请确保DEBUG=True")
    
    logger.info(f"当前页数据: 第{page}页, 偏移量:{offset}, 数据量:{len(tags)}")
    
    # 计算总页数
    total_pages = ceil(total_count / page_size)
    
    # 创建自定义分页信息
    pagination = {
        'page': page,
        'page_size': page_size,
        'has_previous': page > 1,
        'has_next': page < total_pages,
        'total_pages': total_pages,
        'total_count': total_count,
        'previous_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None,
        'page_range': range(max(1, page - 2), min(total_pages + 1, page + 3)),
        'start_index': offset + 1 if total_count > 0 else 0,
        'end_index': min(offset + page_size, total_count),
    }
    
    context = {
        'tags': tags,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'order_by': order_by,
        'section': 'tags',
        'title': _('标签管理'),
        'pagination': pagination,
        'table_name': 'core_gametag',  # 添加表名到模板上下文
        'query_time': f"{query_time:.4f}",  # 添加查询时间到上下文
    }
    
    logger.info(f"标签列表页面渲染完成，返回 {len(tags)} 条记录")
    return render(request, 'admin/tags.html', context)


@login_required
def tag_create(request):
    """创建标签"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            is_active = request.POST.get('is_active', 'false') == 'true'
            
            # 检查标签名是否已存在
            if GameTag.objects.filter(name=name).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': _('标签名已存在')
                })
            
            # 创建标签
            tag = GameTag(
                name=name,
                is_active=is_active
            )
            
            # 尝试保存标签，如果slug冲突则添加随机后缀
            try:
                tag.save()
            except Exception as slug_error:
                if 'UNIQUE constraint' in str(slug_error) and 'slug' in str(slug_error):
                    # 如果是slug唯一性约束错误，则手动设置一个唯一的slug
                    # 使用标签名+时间戳生成唯一hash作为slug
                    hash_text = f"{name}-{time.time()}"
                    hash_obj = hashlib.md5(hash_text.encode('utf-8'))
                    unique_slug = slugify(name)
                    
                    # 如果基础slug无效（比如纯中文），则使用hash值
                    if not unique_slug:
                        unique_slug = hash_obj.hexdigest()[:8]
                    else:
                        # 否则在基础slug后添加hash后缀
                        unique_slug = f"{unique_slug}-{hash_obj.hexdigest()[:6]}"
                    
                    tag.slug = unique_slug
                    tag.save()
                else:
                    # 如果是其他错误，则继续抛出
                    raise
            
            # 新创建的标签肯定没有游戏关联
            games_count = 0
            
            return JsonResponse({
                'status': 'success',
                'message': _('标签创建成功'),
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                    'is_active': tag.is_active,
                    'games_count': games_count
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': _('标签创建失败：{}').format(str(e))
            }, status=500)
            
    # GET请求返回错误
    return JsonResponse({
        'status': 'error',
        'message': _('不支持的请求方法')
    }, status=405)


@login_required
def tag_update(request, tag_id):
    """更新标签"""
    try:
        tag = get_object_or_404(GameTag, id=tag_id)
    except:
        return JsonResponse({
            'status': 'error',
            'message': _('标签不存在')
        }, status=404)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            is_active = request.POST.get('is_active', 'false') == 'true'
            
            # 检查标签名是否已存在（排除当前标签）
            if GameTag.objects.filter(name=name).exclude(id=tag_id).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': _('标签名已存在')
                })
            
            # 更新标签
            tag.name = name
            tag.is_active = is_active
            
            # 处理可能的slug唯一性冲突
            try:
                tag.save()
            except Exception as slug_error:
                if 'UNIQUE constraint' in str(slug_error) and 'slug' in str(slug_error):
                    # 如果是slug唯一性约束错误，则手动设置一个唯一的slug
                    hash_text = f"{name}-{time.time()}"
                    hash_obj = hashlib.md5(hash_text.encode('utf-8'))
                    unique_slug = slugify(name)
                    
                    # 如果基础slug无效（比如纯中文），则使用hash值
                    if not unique_slug:
                        unique_slug = hash_obj.hexdigest()[:8]
                    else:
                        # 否则在基础slug后添加hash后缀
                        unique_slug = f"{unique_slug}-{hash_obj.hexdigest()[:6]}"
                    
                    tag.slug = unique_slug
                    tag.save()
                else:
                    # 如果是其他错误，则继续抛出
                    raise
            
            # 获取游戏计数
            games_count = tag.games.count()
            
            return JsonResponse({
                'status': 'success',
                'message': _('标签更新成功'),
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                    'is_active': tag.is_active,
                    'games_count': games_count
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': _('标签更新失败：{}').format(str(e))
            }, status=500)
    
    # GET请求返回错误
    return JsonResponse({
        'status': 'error',
        'message': _('不支持的请求方法')
    }, status=405)


@login_required
def tag_detail(request, tag_id):
    """获取标签详情"""
    try:
        tag = GameTag.objects.annotate(games_count=Count('games')).get(id=tag_id)
        return JsonResponse({
            'status': 'success',
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'is_active': tag.is_active,
                'games_count': tag.games_count,
            }
        })
    except GameTag.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': _('标签不存在')}, status=404)


@login_required
@require_POST
def tag_delete(request, tag_id):
    """删除标签"""
    tag = get_object_or_404(GameTag, id=tag_id)
    
    try:
        tag_name = tag.name
        # 检查标签是否被使用
        if tag.games.exists():
            return JsonResponse({
                'status': 'error',
                'message': _('无法删除标签"{}"，该标签正在被使用').format(tag_name)
            }, status=400)
            
        tag.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': _('标签"{}"已删除').format(tag_name)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def tag_toggle_status(request, tag_id):
    """切换标签状态（启用/禁用）"""
    tag = get_object_or_404(GameTag, id=tag_id)
    
    try:
        # 切换状态
        tag.is_active = not tag.is_active
        tag.save()
        
        status_text = _('启用') if tag.is_active else _('禁用')
        
        return JsonResponse({
            'status': 'success',
            'message': _('标签已{}').format(status_text),
            'new_status': 'active' if tag.is_active else 'inactive'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def get_all_tags(request):
    """获取所有标签，用于游戏表单中的标签选择"""
    try:
        # 默认只返回活跃的标签
        active_only = request.GET.get('active_only', 'true') == 'true'
        
        tags = GameTag.objects.all().annotate(games_count=Count('games'))
        if active_only:
            tags = tags.filter(is_active=True)
            
        tags = tags.order_by('name')
        
        tags_list = [{
            'id': tag.id, 
            'name': tag.name,
            'is_active': tag.is_active,
            'games_count': tag.games_count
        } for tag in tags]
        
        return JsonResponse({
            'status': 'success',
            'tags': tags_list
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 