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
from django.db import connection

from .game_category import GameCategory
from .game import Game  # 假设有Game模型

# 获取logger
logger = logging.getLogger(__name__)


@login_required
def game_list(request):
    """游戏列表页面"""
    # 获取搜索参数
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    
    # 查询游戏
    games_query = Game.objects.all().prefetch_related('categories')
    
    # 应用搜索过滤
    if search_query:
        games_query = games_query.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # 应用状态过滤
    if status_filter:
        if status_filter == 'online':
            games_query = games_query.filter(status='online')
        elif status_filter == 'offline':
            games_query = games_query.filter(status='offline')
        elif status_filter == 'pending':
            games_query = games_query.filter(status='pending')
    
    # 应用分类过滤
    if category_filter:
        games_query = games_query.filter(categories__id=category_filter)
    
    # 获取排序方式
    order_by = request.GET.get('order_by', '-created_at')
    if order_by not in ['title', 'created_at', 'play_count', '-title', '-created_at', '-play_count']:
        order_by = '-created_at'
    
    games_query = games_query.order_by(order_by)
    
    # 统计游戏总数（用于分页）
    total_count = games_query.count()
    online_count = games_query.filter(status='online').count()
    offline_count = games_query.filter(status='offline').count()
    pending_count = games_query.filter(status='pending').count()
    
    # 数据库层面的分页
    per_page = 10  # 每页显示的游戏数量
    page_num = int(request.GET.get('page', 1))
    offset = (page_num - 1) * per_page
    
    # 应用LIMIT和OFFSET进行数据库分页
    games = games_query[offset:offset+per_page]
    
    # 创建自定义分页对象
    class DatabasePaginator:
        def __init__(self, object_list, number, per_page, count):
            self.object_list = object_list
            self.number = number
            self.per_page = per_page
            self.count = count
            
        @property
        def paginator(self):
            return self
            
        @property
        def has_previous(self):
            return self.number > 1
            
        @property
        def has_next(self):
            return self.number * self.per_page < self.count
            
        @property
        def previous_page_number(self):
            return self.number - 1 if self.has_previous else None
            
        @property
        def next_page_number(self):
            return self.number + 1 if self.has_next else None
            
        @property
        def num_pages(self):
            return (self.count + self.per_page - 1) // self.per_page
            
        @property
        def has_other_pages(self):
            return self.has_previous or self.has_next
            
    # 创建页面对象
    page_obj = DatabasePaginator(games, page_num, per_page, total_count)
    
    # 获取游戏分类（用于筛选）
    categories = GameCategory.objects.filter(is_active=True)
    
    context = {
        'games': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': total_count,
        'online_count': online_count,
        'offline_count': offline_count,
        'pending_count': pending_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'order_by': order_by,
        'categories': categories,
        'section': 'games',
        'title': _('游戏管理'),
    }
    
    return render(request, 'admin/games.html', context)


@login_required
def game_create(request):
    """创建游戏"""
    if request.method == 'POST':
        try:
            data = request.POST
            files = request.FILES
            
            # 创建新游戏
            game = Game(
                title=data.get('title'),
                summary=data.get('summary', ''),
                description=data.get('description', ''),
                iframe_url=data.get('iframe_url', ''),
                iframe_width=data.get('iframe_width', '100%'),
                iframe_height=data.get('iframe_height', '600'),
                status=data.get('status', 'offline'),
                meta_title=data.get('meta_title', ''),
                meta_description=data.get('meta_description', ''),
                meta_keywords=data.get('meta_keywords', ''),
                is_featured=data.get('is_featured') == 'on'
            )
            
            # 处理缩略图
            if 'thumbnail' in files:
                game.thumbnail = files['thumbnail']
            
            # 保存游戏
            game.save()
            
            # 处理分类
            category_id = data.get('category')
            if category_id:
                try:
                    # 确保category_id是整数
                    category_id = int(category_id)
                    # 先清除所有现有分类关系
                    game.categories.clear()
                    category = GameCategory.objects.get(id=category_id)
                    
                    # 使用直接的方式添加关系
                    try:
                        # 使用add方法添加分类
                        game.categories.add(category)
                        logger.info(f"游戏创建 - 使用add方法添加分类成功")
                    except Exception as e:
                        logger.error(f"游戏创建 - add方法失败: {str(e)}")
                        # 如果add方法失败，尝试直接操作数据库
                        with connection.cursor() as cursor:
                            # 添加新关系
                            cursor.execute(
                                "INSERT INTO core_game_categories (game_id, gamecategory_id) VALUES (%s, %s)",
                                [game.id, category.id]
                            )
                        logger.info(f"游戏创建 - 使用SQL直接添加分类关系成功")
                except (ValueError, TypeError) as e:
                    # 如果category_id不是有效的整数，记录错误但不中断流程
                    logger.warning(f"警告: 无效的category_id: {category_id}, 错误: {str(e)}")
                except GameCategory.DoesNotExist:
                    # 如果分类不存在，记录错误但不中断流程
                    logger.warning(f"警告: 找不到ID为{category_id}的分类")
            
            # 处理标签
            tags = data.getlist('tags')
            if tags:
                # 限制标签数量最多为5个
                tags = tags[:5]
                game.tags.set(tags)
            
            # 如果是AJAX请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': _('游戏创建成功')
                })
            
            # 常规表单提交返回重定向
            messages.success(request, _('游戏创建成功'))
            return redirect('admin_panel:game_list')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            
            messages.error(request, _('游戏创建失败：{}').format(str(e)))
    
    # 获取游戏分类（用于表单）
    categories = GameCategory.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
        'section': 'games',
        'title': _('添加游戏'),
    }
    
    return render(request, 'admin/game_form.html', context)


@login_required
def game_update(request, game_id):
    """更新游戏"""
    game = get_object_or_404(Game, id=game_id)
    
    if request.method == 'POST':
        try:
            data = request.POST
            files = request.FILES
            
            # 调试信息：打印关键数据
            logger.debug(f"游戏更新 - 游戏ID: {game_id}")
            logger.debug(f"游戏更新 - 标题: {data.get('title')}")
            logger.debug(f"游戏更新 - 原始分类数据: {data.get('category')}")
            
            # 更新游戏信息
            game.title = data.get('title')
            game.summary = data.get('summary', '')
            game.description = data.get('description', '')
            game.iframe_url = data.get('iframe_url', '')
            game.iframe_width = data.get('iframe_width', '100%')
            game.iframe_height = data.get('iframe_height', '600')
            game.status = data.get('status', 'offline')
            game.meta_title = data.get('meta_title', '')
            game.meta_description = data.get('meta_description', '')
            game.meta_keywords = data.get('meta_keywords', '')
            game.is_featured = data.get('is_featured') == 'on'
            
            # 处理缩略图
            if 'thumbnail' in files:
                game.thumbnail = files['thumbnail']
            
            # 保存游戏
            game.save()
            
            # 处理分类
            category_id = data.get('category')
            logger.debug(f"游戏更新 - 分类ID: {category_id}")
            
            if category_id:
                try:
                    # 确保category_id是整数
                    category_id = int(category_id)
                    logger.debug(f"游戏更新 - 转换后的分类ID: {category_id}")
                    
                    # 先清除所有现有分类关系
                    game.categories.clear()
                    logger.debug(f"游戏更新 - 已清除现有分类")
                    
                    # 获取分类对象
                    category = GameCategory.objects.get(id=category_id)
                    logger.debug(f"游戏更新 - 找到分类: {category.name}, ID: {category.id}")
                    
                    # 使用直接的方式添加关系
                    try:
                        # 使用add方法添加分类
                        game.categories.add(category)
                        logger.info(f"游戏更新 - 使用add方法添加分类成功")
                    except Exception as e:
                        logger.error(f"游戏更新 - add方法失败: {str(e)}")
                        # 如果add方法失败，尝试直接操作数据库
                        with connection.cursor() as cursor:
                            # 清除现有关系
                            cursor.execute(
                                "DELETE FROM core_game_categories WHERE game_id = %s",
                                [game.id]
                            )
                            # 添加新关系
                            cursor.execute(
                                "INSERT INTO core_game_categories (game_id, gamecategory_id) VALUES (%s, %s)",
                                [game.id, category.id]
                            )
                        logger.info(f"游戏更新 - 使用SQL直接添加分类关系成功")
                except (ValueError, TypeError) as e:
                    # 如果category_id不是有效的整数，记录错误但不中断流程
                    logger.warning(f"警告: 无效的category_id: {category_id}, 错误: {str(e)}")
                except GameCategory.DoesNotExist:
                    # 如果分类不存在，记录错误但不中断流程
                    logger.warning(f"警告: 找不到ID为{category_id}的分类")
            
            # 处理标签
            tags = data.getlist('tags')
            if tags:
                # 限制标签数量最多为5个
                tags = tags[:5]
                game.tags.set(tags)
            
            # 如果是AJAX请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': _('游戏更新成功')
                })
            
            # 常规表单提交返回重定向
            messages.success(request, _('游戏更新成功'))
            return redirect('admin_panel:game_list')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            
            messages.error(request, _('游戏更新失败：{}').format(str(e)))
    
    # 获取游戏分类（用于表单）
    categories = GameCategory.objects.filter(is_active=True)
    
    context = {
        'game': game,
        'categories': categories,
        'section': 'games',
        'title': _('编辑游戏'),
    }
    
    return render(request, 'admin/game_form.html', context)


@login_required
def game_detail(request, game_id):
    """获取游戏详情"""
    try:
        game = Game.objects.get(id=game_id)
        
        # 获取标签名称列表
        tag_names = list(game.tags.values_list('name', flat=True))
        
        # 获取分类ID和名称
        categories = list(game.categories.all())
        category_id = categories[0].id if categories else None
        category_name = categories[0].name if categories else ''
        
        # 调试信息
        logger.debug(f"游戏详情 - 游戏ID: {game_id}")
        logger.debug(f"游戏详情 - 分类数量: {len(categories)}")
        logger.debug(f"游戏详情 - 分类ID: {category_id}")
        logger.debug(f"游戏详情 - 分类名称: {category_name}")
        
        # 获取所有分类信息
        category_list = [{'id': cat.id, 'name': cat.name} for cat in categories]
        logger.debug(f"游戏详情 - 分类列表: {category_list}")
        
        # 格式化添加日期
        added_date = game.created_at.strftime('%Y-%m-%d') if game.created_at else ''
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': game.id,
                'title': game.title,
                'summary': game.summary,
                'description': game.description,
                'category_id': category_id,  # 兼容旧代码，使用第一个分类
                'category_name': category_name,  # 兼容旧代码，使用第一个分类
                'categories': category_list,  # 所有分类的列表
                'iframe_url': game.iframe_url,
                'iframe_width': game.iframe_width,
                'iframe_height': game.iframe_height,
                'status': game.status,
                'thumbnail_url': game.thumbnail.url if game.thumbnail else '',
                'tags': list(game.tags.values_list('id', flat=True)),
                'tag_names': tag_names,
                'play_count': game.play_count,
                'rating': game.rating,
                'created_at': added_date,
                'meta_title': game.meta_title if hasattr(game, 'meta_title') else '',
                'meta_description': game.meta_description if hasattr(game, 'meta_description') else '',
                'meta_keywords': game.meta_keywords if hasattr(game, 'meta_keywords') else '',
            }
        })
    except Game.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': _('游戏不存在')}, status=404)


@login_required
@require_POST
def game_delete(request, game_id):
    """删除游戏"""
    game = get_object_or_404(Game, id=game_id)
    
    try:
        game_name = game.title
        game.delete()
        
        # 可以添加日志记录
        
        return JsonResponse({
            'status': 'success',
            'message': _('游戏"{}"已删除').format(game_name)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def game_toggle_status(request, game_id):
    """切换游戏状态（上线/下线）"""
    game = get_object_or_404(Game, id=game_id)
    
    try:
        new_status = request.POST.get('status')
        if new_status in ['online', 'offline', 'pending']:
            old_status = game.status
            game.status = new_status
            game.save()
            
            status_text = {
                'online': _('上线'),
                'offline': _('下线'),
                'pending': _('待审核')
            }
            
            # 可以添加日志记录
            
            return JsonResponse({
                'status': 'success', 
                'message': _('游戏已{}').format(status_text[new_status]),
                'new_status': new_status
            })
        else:
            return JsonResponse({
                'status': 'error', 
                'message': _('无效的状态值')
            }, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500) 