from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Game, Category
import logging
import traceback
import json

# 获取日志记录器
logger = logging.getLogger(__name__)

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
@csrf_exempt  # 添加CSRF豁免，避免CSRF错误
def game_edit_json(request, game_id):
    """
    获取游戏数据的JSON API，用于编辑游戏模态框
    """
    try:
        logger.info(f"Fetching game data for ID: {game_id}, User: {request.user.username}")
        
        # 检查请求头
        logger.debug(f"Request headers: {request.headers}")
        
        game = get_object_or_404(Game, pk=game_id)
        logger.debug(f"Game found: {game.title} (ID: {game_id})")
        
        # 准备游戏数据的JSON响应
        data = {
            'id': game.id,
            'title': game.title,
            'slug': game.slug,
            'description': game.description,
            'is_active': game.is_active,
            'is_featured': game.is_featured,
            'categories': [{'id': category.id, 'name': category.name} for category in game.categories.all()],
            'game_url': game.iframe_url,  # 将iframe_url映射为game_url
            'game_width': '100%',  # 这些字段在模型中不存在，使用默认值
            'game_height': '600px',
            'created_at': game.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': game.updated_at.strftime('%Y-%m-%d %H:%M:%S') if game.updated_at else None,
            'view_count': game.view_count,
            'rating': float(game.rating) if game.rating is not None else 0.0
        }
        
        # 添加缩略图URL，如果存在
        if game.thumbnail:
            data['thumbnail_url'] = game.thumbnail.url
            logger.debug(f"Thumbnail URL: {game.thumbnail.url}")
        else:
            data['thumbnail_url'] = None
            logger.debug("No thumbnail found")
        
        # 添加标签数据，如果有标签字段
        try:
            data['tags'] = list(game.tags.names())
            logger.debug(f"Tags: {data['tags']}")
        except AttributeError as e:
            logger.warning(f"No tags field found: {e}")
            data['tags'] = []
        
        logger.info(f"Successfully prepared game data for ID: {game_id}")
        
        # 创建响应对象并设置正确的内容类型
        response = JsonResponse(data)
        response["Content-Type"] = "application/json; charset=utf-8"
        return response
    
    except Exception as e:
        logger.error(f"Error fetching game data for ID {game_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 创建错误响应并设置正确的内容类型
        response = JsonResponse({
            'error': 'An error occurred while fetching game data',
            'message': str(e),
            'type': type(e).__name__
        }, status=500)
        response["Content-Type"] = "application/json; charset=utf-8"
        return response 

@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
@csrf_exempt
def toggle_game_status(request, game_id):
    """
    切换游戏的激活状态
    """
    try:
        logger.info(f"Toggle game status for ID: {game_id}, User: {request.user.username}")
        
        game = get_object_or_404(Game, pk=game_id)
        logger.debug(f"Game found: {game.title} (ID: {game_id}), current status: {game.is_active}")
        
        # 切换状态
        game.is_active = not game.is_active
        game.save(update_fields=['is_active'])
        
        logger.info(f"Game status toggled for ID: {game_id}, new status: {game.is_active}")
        
        return JsonResponse({
            'success': True,
            'game_id': game.id,
            'is_active': game.is_active,
            'status_text': _('Active') if game.is_active else _('Inactive')
        })
        
    except Exception as e:
        logger.error(f"Error toggling game status for ID {game_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while toggling game status',
            'message': str(e),
            'type': type(e).__name__
        }, status=500) 

@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
def add_category_modal(request):
    """
    通过模态框添加分类
    """
    try:
        logger.info(f"Adding category via modal form, User: {request.user.username}")
        
        # 获取表单数据
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        parent_id = request.POST.get('parent')
        is_active = request.POST.get('is_active') == 'on'
        icon_class = request.POST.get('icon_class', '')

        # 验证必填字段
        if not name:
            logger.warning("Category creation failed: Name is missing")
            return JsonResponse({
                'success': False,
                'message': _('Name is required')
            }, status=400)
        
        # 处理父级分类
        parent = None
        if parent_id and parent_id != '0':
            parent = get_object_or_404(Category, pk=parent_id)
        
        # 创建新分类（slug将由模型的save方法自动生成）
        category = Category.objects.create(
            name=name,
            description=description,
            parent=parent,
            is_active=is_active,
            icon_class=icon_class
        )
        
        logger.info(f"Category created successfully: {category.name} (ID: {category.id})")
        
        # 如果是AJAX请求，返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Category added successfully'),
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'parent': category.parent.name if category.parent else None,
                    'is_active': category.is_active
                }
            })
        
        # 否则重定向回分类列表页面
        return HttpResponseRedirect(reverse('admin:games_category_changelist'))
        
    except Exception as e:
        logger.error(f"Error adding category: {str(e)}")
        logger.error(traceback.format_exc())
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('An error occurred while adding the category'),
                'error': str(e)
            }, status=500)
        
        # 重定向回分类列表页面，并显示错误消息
        return HttpResponseRedirect(reverse('admin:games_category_changelist')) 

@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def get_category_data(request, category_id):
    """
    获取分类数据的JSON API，用于编辑分类模态框
    """
    try:
        logger.info(f"Fetching category data for ID: {category_id}, User: {request.user.username}")
        
        category = get_object_or_404(Category, pk=category_id)
        logger.debug(f"Category found: {category.name} (ID: {category_id})")
        
        # 准备分类数据的JSON响应
        data = {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'parent_id': category.parent.id if category.parent else 0,
            'is_active': category.is_active,
            'icon_class': category.icon_class
        }
        
        logger.info(f"Successfully prepared category data for ID: {category_id}")
        
        return JsonResponse(data)
    
    except Exception as e:
        logger.error(f"Error fetching category data for ID {category_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            'error': 'An error occurred while fetching category data',
            'message': str(e),
            'type': type(e).__name__
        }, status=500)

@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
def edit_category_modal(request, category_id):
    """
    通过模态框编辑分类
    """
    try:
        logger.info(f"Editing category via modal form, ID: {category_id}, User: {request.user.username}")
        
        # 获取分类对象
        category = get_object_or_404(Category, pk=category_id)
        
        # 获取表单数据
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        parent_id = request.POST.get('parent')
        is_active = request.POST.get('is_active') == 'on'
        icon_class = request.POST.get('icon_class', '')

        # 验证必填字段
        if not name:
            logger.warning("Category update failed: Name is missing")
            return JsonResponse({
                'success': False,
                'message': _('Name is required')
            }, status=400)
        
        # 处理父级分类
        parent = None
        if parent_id and parent_id != '0':
            # 确保不会将分类设置为自己的子分类
            if int(parent_id) == category.id:
                logger.warning(f"Category update failed: Cannot set category as its own parent")
                return JsonResponse({
                    'success': False,
                    'message': _('A category cannot be its own parent')
                }, status=400)
            parent = get_object_or_404(Category, pk=parent_id)
        
        # 更新分类（如果名称改变，slug将由模型的save方法自动重新生成）
        old_name = category.name
        category.name = name
        category.description = description
        category.parent = parent
        category.is_active = is_active
        category.icon_class = icon_class

        # 如果名称改变了，清空slug让模型重新生成
        if old_name != name:
            category.slug = ''

        category.save()
        
        logger.info(f"Category updated successfully: {category.name} (ID: {category.id})")
        
        # 如果是AJAX请求，返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Category updated successfully'),
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'parent': category.parent.name if category.parent else None,
                    'is_active': category.is_active
                }
            })
        
        # 否则重定向回分类列表页面
        return HttpResponseRedirect(reverse('admin:games_category_changelist'))
        
    except Exception as e:
        logger.error(f"Error updating category: {str(e)}")
        logger.error(traceback.format_exc())
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('An error occurred while updating the category'),
                'error': str(e)
            }, status=500)
        
        # 重定向回分类列表页面，并显示错误消息
        return HttpResponseRedirect(reverse('admin:games_category_changelist')) 

@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def view_category_modal(request, category_id):
    """
    获取分类详情的JSON API，用于查看分类模态框
    """
    try:
        logger.info(f"Viewing category details, ID: {category_id}, User: {request.user.username}")
        
        category = get_object_or_404(Category, pk=category_id)
        logger.debug(f"Category found: {category.name} (ID: {category_id})")
        
        # 准备分类数据的JSON响应
        data = {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'parent': category.parent.name if category.parent else None,
            'parent_id': category.parent.id if category.parent else 0,
            'is_active': category.is_active,
            'created_at': category.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': category.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'game_count': category.games.count(),
            'icon_class': category.icon_class
        }
        
        # 添加图片URL，如果存在
        if category.image:
            data['image_url'] = category.image.url
        else:
            data['image_url'] = None
        
        # 获取该分类下的游戏列表（最多10个）
        games = category.games.all()[:10]
        data['games'] = [{
            'id': game.id,
            'title': game.title,
            'slug': game.slug,
            'is_active': game.is_active
        } for game in games]
        
        logger.info(f"Successfully prepared category details for ID: {category_id}")
        
        return JsonResponse(data)
    
    except Exception as e:
        logger.error(f"Error fetching category details for ID {category_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            'error': 'An error occurred while fetching category details',
            'message': str(e),
            'type': type(e).__name__
        }, status=500) 

@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
def delete_category_modal(request, category_id):
    """
    通过模态框删除分类
    """
    try:
        logger.info(f"Deleting category, ID: {category_id}, User: {request.user.username}")
        
        category = get_object_or_404(Category, pk=category_id)
        logger.debug(f"Category found: {category.name} (ID: {category_id})")
        
        # 检查是否有游戏使用此分类
        game_count = category.games.count()
        if game_count > 0:
            logger.warning(f"Cannot delete category: {category.name} (ID: {category_id}) - has {game_count} games")
            return JsonResponse({
                'success': False,
                'message': _('Cannot delete category that has games. Remove games from this category first.'),
                'game_count': game_count
            }, status=400)
        
        # 检查是否有子分类
        children_count = Category.objects.filter(parent=category).count()
        if children_count > 0:
            logger.warning(f"Cannot delete category: {category.name} (ID: {category_id}) - has {children_count} children")
            return JsonResponse({
                'success': False,
                'message': _('Cannot delete category that has subcategories. Remove subcategories first.'),
                'children_count': children_count
            }, status=400)
        
        # 获取名称以便在日志中使用
        category_name = category.name
        category_id_log = category.id
        
        # 删除分类
        category.delete()
        
        logger.info(f"Category deleted successfully: {category_name} (ID: {category_id_log})")
        
        # 如果是AJAX请求，返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Category deleted successfully')
            })
        
        # 否则重定向回分类列表页面
        return HttpResponseRedirect(reverse('admin:games_category_changelist'))
        
    except Exception as e:
        logger.error(f"Error deleting category: {str(e)}")
        logger.error(traceback.format_exc())
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('An error occurred while deleting the category'),
                'error': str(e)
            }, status=500)
        
        # 重定向回分类列表页面，并显示错误消息
        return HttpResponseRedirect(reverse('admin:games_category_changelist')) 

@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
def add_user_modal(request):
    """
    通过模态框添加用户
    """
    try:
        logger.info(f"Adding user via modal form, User: {request.user.username}")
        
        # 检查是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # 创建UserCreationForm实例
        form = UserCreationForm(request.POST)
        
        # 验证表单
        if form.is_valid():
            # 保存用户
            user = form.save()
            logger.info(f"User created successfully: {user.username} (ID: {user.id})")
            
            # 如果是AJAX请求，返回成功消息
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': _('User added successfully'),
                    'redirect_url': reverse('admin:auth_user_changelist')
                })
            
            # 否则重定向到用户列表页面
            return HttpResponseRedirect(reverse('admin:auth_user_changelist'))
        else:
            # 表单验证失败
            logger.warning(f"User creation failed: {form.errors}")
            
            # 如果是AJAX请求，返回错误信息
            if is_ajax:
                # 返回表单错误
                return render(request, 'admin/auth/user/add_form.html', {
                    'form': form,
                })
            
            # 否则重定向回添加用户页面
            return render(request, 'admin/auth/user/add.html', {
                'form': form,
            })
            
    except Exception as e:
        logger.error(f"Error adding user: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 如果是AJAX请求，返回错误信息
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while adding user',
                'message': str(e),
                'type': type(e).__name__
            }, status=500)
        
        # 否则重定向回添加用户页面
        return HttpResponseRedirect(reverse('admin:auth_user_add')) 