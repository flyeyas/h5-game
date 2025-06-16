from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from .models import Game, Category
import logging
import traceback
import json

# Get logger
logger = logging.getLogger(__name__)

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
@csrf_exempt  # Add CSRF exemption to avoid CSRF errors
def game_edit_json(request, game_id):
    """
    JSON API to get game data for editing game modal
    """
    try:
        logger.info(f"Fetching game data for ID: {game_id}, User: {request.user.username}")
        
        # Check request headers
        logger.debug(f"Request headers: {request.headers}")

        game = get_object_or_404(Game, pk=game_id)
        logger.debug(f"Game found: {game.title} (ID: {game_id})")

        # Prepare JSON response for game data
        data = {
            'id': game.id,
            'title': game.title,
            'slug': game.slug,
            'description': game.description,
            'is_active': game.is_active,
            'is_featured': game.is_featured,
            'categories': [{'id': category.id, 'name': category.name} for category in game.categories.all()],
            'game_url': game.iframe_url,  # Map iframe_url to game_url
            'game_width': '100%',  # These fields don't exist in the model, use default values
            'game_height': '600px',
            'created_at': game.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': game.updated_at.strftime('%Y-%m-%d %H:%M:%S') if game.updated_at else None,
            'view_count': game.view_count,
            'rating': float(game.rating) if game.rating is not None else 0.0
        }
        
        # Add thumbnail URL if exists
        if game.thumbnail:
            data['thumbnail_url'] = game.thumbnail.url
            logger.debug(f"Thumbnail URL: {game.thumbnail.url}")
        else:
            data['thumbnail_url'] = None
            logger.debug("No thumbnail found")
        
        # Add tag data if tag field exists
        try:
            data['tags'] = list(game.tags.names())
            logger.debug(f"Tags: {data['tags']}")
        except AttributeError as e:
            logger.warning(f"No tags field found: {e}")
            data['tags'] = []
        
        logger.info(f"Successfully prepared game data for ID: {game_id}")
        
        # Create response object and set correct content type
        response = JsonResponse(data)
        response["Content-Type"] = "application/json; charset=utf-8"
        return response
    
    except Exception as e:
        logger.error(f"Error fetching game data for ID {game_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Create error response and set correct content type
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
    Add category through modal
    """
    try:
        logger.info(f"Adding category via modal form, User: {request.user.username}")

        # Get form data
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
        
        # Handle parent category
        parent = None
        if parent_id and parent_id != '0':
            parent = get_object_or_404(Category, pk=parent_id)

        # Create new category (slug will be automatically generated by model's save method)
        category = Category.objects.create(
            name=name,
            description=description,
            parent=parent,
            is_active=is_active,
            icon_class=icon_class
        )
        
        logger.info(f"Category created successfully: {category.name} (ID: {category.id})")

        # If it's an AJAX request, return JSON response
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
        
        # Otherwise redirect back to category list page
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
    JSON API to get category data for editing category modal
    """
    try:
        logger.info(f"Fetching category data for ID: {category_id}, User: {request.user.username}")
        
        category = get_object_or_404(Category, pk=category_id)
        logger.debug(f"Category found: {category.name} (ID: {category_id})")

        # Prepare JSON response for category data
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
    Edit category through modal
    """
    try:
        logger.info(f"Editing category via modal form, ID: {category_id}, User: {request.user.username}")

        # Get category object
        category = get_object_or_404(Category, pk=category_id)

        # Get form data
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
        
        # Handle parent category
        parent = None
        if parent_id and parent_id != '0':
            # Ensure category cannot be set as its own subcategory
            if int(parent_id) == category.id:
                logger.warning(f"Category update failed: Cannot set category as its own parent")
                return JsonResponse({
                    'success': False,
                    'message': _('A category cannot be its own parent')
                }, status=400)
            parent = get_object_or_404(Category, pk=parent_id)
        
        # Update category (if name changes, slug will be automatically regenerated by model's save method)
        old_name = category.name
        category.name = name
        category.description = description
        category.parent = parent
        category.is_active = is_active
        category.icon_class = icon_class

        # If name changed, clear slug to let model regenerate it
        if old_name != name:
            category.slug = ''

        category.save()
        
        logger.info(f"Category updated successfully: {category.name} (ID: {category.id})")

        # If it's an AJAX request, return JSON response
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
        
        # Otherwise redirect back to category list page
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
    JSON API to get category details for viewing category modal
    """
    try:
        logger.info(f"Viewing category details, ID: {category_id}, User: {request.user.username}")
        
        category = get_object_or_404(Category, pk=category_id)
        logger.debug(f"Category found: {category.name} (ID: {category_id})")

        # Prepare JSON response for category data
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
        
        # Add image URL if exists
        if category.image:
            data['image_url'] = category.image.url
        else:
            data['image_url'] = None
        
        # Get game list under this category (maximum 10)
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
        
        # Check if any games are using this category
        game_count = category.games.count()
        if game_count > 0:
            logger.warning(f"Cannot delete category: {category.name} (ID: {category_id}) - has {game_count} games")
            return JsonResponse({
                'success': False,
                'message': _('Cannot delete category that has games. Remove games from this category first.'),
                'game_count': game_count
            }, status=400)

        # Check if there are subcategories
        children_count = Category.objects.filter(parent=category).count()
        if children_count > 0:
            logger.warning(f"Cannot delete category: {category.name} (ID: {category_id}) - has {children_count} children")
            return JsonResponse({
                'success': False,
                'message': _('Cannot delete category that has subcategories. Remove subcategories first.'),
                'children_count': children_count
            }, status=400)
        
        # Get name for use in logs
        category_name = category.name
        category_id_log = category.id

        # Delete category
        category.delete()

        logger.info(f"Category deleted successfully: {category_name} (ID: {category_id_log})")

        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Category deleted successfully')
            })
        
        # Otherwise redirect back to category list page
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
    Add user through modal
    """
    try:
        logger.info(f"Adding user via modal form, User: {request.user.username}")

        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Create UserCreationForm instance
        form = UserCreationForm(request.POST)

        # Validate form
        if form.is_valid():
            # Save user
            user = form.save()
            logger.info(f"User created successfully: {user.username} (ID: {user.id})")

            # If it's an AJAX request, return success message
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': _('User added successfully'),
                    'redirect_url': reverse('admin:auth_user_changelist')
                })
            
            # Otherwise redirect to user list page
            return HttpResponseRedirect(reverse('admin:auth_user_changelist'))
        else:
            # Form validation failed
            logger.warning(f"User creation failed: {form.errors}")

            # If it's an AJAX request, return error information
            if is_ajax:
                # Return form errors
                return render(request, 'admin/auth/user/add_form.html', {
                    'form': form,
                })

            # Otherwise redirect back to add user page
            return render(request, 'admin/auth/user/add.html', {
                'form': form,
            })
            
    except Exception as e:
        logger.error(f"Error adding user: {str(e)}")
        logger.error(traceback.format_exc())
        
        # If it's an AJAX request, return error information
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while adding user',
                'message': str(e),
                'type': type(e).__name__
            }, status=500)

        # Otherwise redirect back to add user page
        return HttpResponseRedirect(reverse('admin:auth_user_add'))


@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
@csrf_exempt
def toggle_category_status(request, category_id):
    """
    切换分类的激活状态
    """
    try:
        logger.info(f"Toggle category status for ID: {category_id}, User: {request.user.username}")

        category = get_object_or_404(Category, pk=category_id)
        logger.debug(f"Category found: {category.name} (ID: {category_id}), current status: {category.is_active}")

        # 切换状态
        category.is_active = not category.is_active
        category.save(update_fields=['is_active'])

        logger.info(f"Category status toggled for ID: {category_id}, new status: {category.is_active}")

        return JsonResponse({
            'success': True,
            'category_id': category.id,
            'is_active': category.is_active,
            'status_text': _('Active') if category.is_active else _('Inactive'),
            'message': _('Category status updated successfully')
        })

    except Exception as e:
        logger.error(f"Error toggling category status for ID {category_id}: {str(e)}")
        logger.error(traceback.format_exc())

        return JsonResponse({
            'success': False,
            'error': 'An error occurred while toggling category status',
            'message': str(e),
            'type': type(e).__name__
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
@csrf_exempt
def toggle_user_staff(request, user_id):
    """
    Toggle user's staff status, but protect user with ID=1
    """
    try:
        logger.info(f"Toggle user staff status for ID: {user_id}, User: {request.user.username}")

        # Get User model
        User = get_user_model()
        user = get_object_or_404(User, pk=user_id)
        logger.debug(f"User found: {user.username} (ID: {user_id}), current staff status: {user.is_staff}")

        # Check if it's the user with ID=1
        if user.id == 1:
            logger.warning(f"Attempt to modify staff status of protected user ID: {user_id}")
            return JsonResponse({
                'success': False,
                'message': _('Cannot modify staff status of the primary administrator account'),
                'error': 'Protected user'
            }, status=403)

        # 解析请求数据
        try:
            data = json.loads(request.body)
            new_staff_status = data.get('is_staff', not user.is_staff)
        except (json.JSONDecodeError, KeyError):
            new_staff_status = not user.is_staff

        # 更新staff状态
        user.is_staff = new_staff_status
        user.save(update_fields=['is_staff'])

        logger.info(f"User staff status toggled for ID: {user_id}, new status: {user.is_staff}")

        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'is_staff': user.is_staff,
            'status_text': _('Yes') if user.is_staff else _('No'),
            'message': _('Staff status updated successfully')
        })

    except Exception as e:
        logger.error(f"Error toggling user staff status for ID {user_id}: {str(e)}")
        logger.error(traceback.format_exc())

        return JsonResponse({
            'success': False,
            'error': 'An error occurred while toggling user staff status',
            'message': str(e),
            'type': type(e).__name__
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
@csrf_exempt
def toggle_user_superuser(request, user_id):
    """
    Toggle user's superuser status, but protect user with ID=1
    """
    try:
        logger.info(f"Toggle user superuser status for ID: {user_id}, User: {request.user.username}")

        # Get User model
        User = get_user_model()
        user = get_object_or_404(User, pk=user_id)
        logger.debug(f"User found: {user.username} (ID: {user_id}), current superuser status: {user.is_superuser}")

        # Check if it's the user with ID=1
        if user.id == 1:
            logger.warning(f"Attempt to modify superuser status of protected user ID: {user_id}")
            return JsonResponse({
                'success': False,
                'message': _('Cannot modify superuser status of the primary administrator account'),
                'error': 'Protected user'
            }, status=403)

        # 解析请求数据
        try:
            data = json.loads(request.body)
            new_superuser_status = data.get('is_superuser', not user.is_superuser)
        except (json.JSONDecodeError, KeyError):
            new_superuser_status = not user.is_superuser

        # 更新superuser状态
        user.is_superuser = new_superuser_status
        user.save(update_fields=['is_superuser'])

        logger.info(f"User superuser status toggled for ID: {user_id}, new status: {user.is_superuser}")

        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'is_superuser': user.is_superuser,
            'status_text': _('Yes') if user.is_superuser else _('No'),
            'message': _('Superuser status updated successfully')
        })

    except Exception as e:
        logger.error(f"Error toggling user superuser status for ID {user_id}: {str(e)}")
        logger.error(traceback.format_exc())

        return JsonResponse({
            'success': False,
            'error': 'An error occurred while toggling user superuser status',
            'message': str(e),
            'type': type(e).__name__
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
@csrf_exempt
def toggle_user_active(request, user_id):
    """
    Toggle user's active status, but protect user with ID=1
    """
    try:
        logger.info(f"Toggle user active status for ID: {user_id}, User: {request.user.username}")

        # Get User model
        User = get_user_model()
        user = get_object_or_404(User, pk=user_id)
        logger.debug(f"User found: {user.username} (ID: {user_id}), current active status: {user.is_active}")

        # Check if it's the user with ID=1
        if user.id == 1:
            logger.warning(f"Attempt to modify active status of protected user ID: {user_id}")
            return JsonResponse({
                'success': False,
                'message': _('Cannot modify active status of the primary administrator account'),
                'error': 'Protected user'
            }, status=403)

        # 解析请求数据
        try:
            data = json.loads(request.body)
            new_active_status = data.get('is_active', not user.is_active)
        except (json.JSONDecodeError, KeyError):
            new_active_status = not user.is_active

        # 更新active状态
        user.is_active = new_active_status
        user.save(update_fields=['is_active'])

        logger.info(f"User active status toggled for ID: {user_id}, new status: {user.is_active}")

        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'is_active': user.is_active,
            'status_text': _('Yes') if user.is_active else _('No'),
            'message': _('Active status updated successfully')
        })

    except Exception as e:
        logger.error(f"Error toggling user active status for ID {user_id}: {str(e)}")
        logger.error(traceback.format_exc())

        return JsonResponse({
            'success': False,
            'error': 'An error occurred while toggling user active status',
            'message': str(e),
            'type': type(e).__name__
        }, status=500)

@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def get_permissions_api(request):
    """
    API endpoint to get all permissions for user group management modal
    """
    try:
        logger.info(f"Fetching permissions data, User: {request.user.username}")

        # Get all permissions, sorted by content type and permission name
        permissions = Permission.objects.select_related('content_type').order_by(
            'content_type__app_label',
            'content_type__model',
            'codename'
        )

        # Prepare permissions data
        permissions_data = []
        for permission in permissions:
            # Get readable name of content type
            content_type = permission.content_type
            app_label = content_type.app_label
            model_name = content_type.model

            # Set group name based on app label
            if app_label == 'auth':
                group_name = _('Authentication and Authorization')
            elif app_label == 'admin':
                group_name = _('Administration')
            elif app_label == 'contenttypes':
                group_name = _('Content Types')
            elif app_label == 'sessions':
                group_name = _('Sessions')
            elif app_label == 'sites':
                group_name = _('Sites')
            elif app_label == 'games':
                group_name = _('Game Management')  # Game Management
            else:
                group_name = app_label.title()

            # Get readable name of model
            try:
                model_class = content_type.model_class()
                if model_class and hasattr(model_class._meta, 'verbose_name'):
                    model_verbose_name = str(model_class._meta.verbose_name)
                else:
                    model_verbose_name = model_name
            except:
                model_verbose_name = model_name

            # 构建权限显示名称
            permission_display = f"{group_name} | {model_verbose_name} | {permission.name}"

            permissions_data.append({
                'id': permission.id,
                'name': permission_display,
                'codename': permission.codename,
                'content_type': {
                    'app_label': app_label,
                    'model': model_name,
                    'name': model_verbose_name
                },
                'group': group_name
            })

        logger.info(f"Successfully prepared {len(permissions_data)} permissions")

        return JsonResponse({
            'success': True,
            'permissions': permissions_data,
            'count': len(permissions_data)
        })

    except Exception as e:
        logger.error(f"Error fetching permissions data: {str(e)}")
        logger.error(traceback.format_exc())

        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching permissions data',
            'message': str(e),
            'type': type(e).__name__
        }, status=500)

@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
def add_group_modal(request):
    """
    Add user group through modal
    """
    try:
        logger.info(f"Adding group via modal form, User: {request.user.username}")

        # Get form data
        name = request.POST.get('name')
        permissions_ids = request.POST.getlist('permissions')

        # Validate required fields
        if not name:
            logger.warning("Group creation failed: Name is missing")
            return JsonResponse({
                'success': False,
                'message': _('Name is required')
            }, status=400)

        # Check if group name already exists
        if Group.objects.filter(name=name).exists():
            logger.warning(f"Group creation failed: Name '{name}' already exists")
            return JsonResponse({
                'success': False,
                'message': _('A group with this name already exists')
            }, status=400)

        # Create new user group
        group = Group.objects.create(name=name)

        # Add permissions
        if permissions_ids:
            permissions = Permission.objects.filter(id__in=permissions_ids)
            group.permissions.set(permissions)
            logger.info(f"Added {len(permissions)} permissions to group: {group.name}")

        logger.info(f"Group created successfully: {group.name} (ID: {group.id})")

        # Create Django admin history record
        try:
            LogEntry.objects.create(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(Group).pk,
                object_id=group.pk,
                object_repr=str(group),
                action_flag=ADDITION,
                change_message=_('Added group via modal form.')
            )
            logger.info(f"Created admin log entry for group addition: {group.name}")
        except Exception as log_error:
            logger.warning(f"Failed to create admin log entry for group {group.name}: {log_error}")

        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Group added successfully'),
                'group': {
                    'id': group.id,
                    'name': group.name,
                    'permissions_count': group.permissions.count()
                }
            })

        # Otherwise redirect back to user group list page
        return HttpResponseRedirect(reverse('admin:auth_group_changelist'))

    except Exception as e:
        logger.error(f"Error adding group: {str(e)}")
        logger.error(traceback.format_exc())

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('An error occurred while adding the group'),
                'error': str(e)
            }, status=500)

        # 重定向回用户组列表页面，并显示错误消息
        return HttpResponseRedirect(reverse('admin:auth_group_changelist'))


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def get_group_data(request, group_id):
    """
    JSON API to get user group data for editing user group modal
    """
    try:
        logger.info(f"Fetching group data for ID: {group_id}, User: {request.user.username}")

        group = get_object_or_404(Group, pk=group_id)
        logger.debug(f"Group found: {group.name} (ID: {group_id})")

        # Prepare JSON response for user group data
        data = {
            'id': group.id,
            'name': group.name,
            'permissions': list(group.permissions.values_list('id', flat=True))
        }

        logger.info(f"Successfully prepared group data for ID: {group_id}")

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error fetching group data for ID {group_id}: {str(e)}")
        logger.error(traceback.format_exc())

        return JsonResponse({
            'error': 'An error occurred while fetching group data',
            'message': str(e),
            'type': type(e).__name__
        }, status=500)


@login_required
@user_passes_test(is_staff)
@require_http_methods(["POST"])
def edit_group_modal(request, group_id):
    """
    Edit user group through modal
    """
    try:
        logger.info(f"Editing group via modal form, ID: {group_id}, User: {request.user.username}")

        # Get user group object
        group = get_object_or_404(Group, pk=group_id)

        # Get form data
        name = request.POST.get('name')
        permissions_ids = request.POST.getlist('permissions')

        # Validate required fields
        if not name:
            logger.warning("Group update failed: Name is missing")
            return JsonResponse({
                'success': False,
                'message': _('Name is required')
            }, status=400)

        # Check if group name already exists (excluding current group)
        if Group.objects.filter(name=name).exclude(id=group_id).exists():
            logger.warning(f"Group update failed: Name '{name}' already exists")
            return JsonResponse({
                'success': False,
                'message': _('A group with this name already exists')
            }, status=400)

        # 记录原始数据用于变更消息
        original_name = group.name
        original_permissions = set(group.permissions.all())
        original_permissions_count = len(original_permissions)

        # 更新用户组信息
        group.name = name
        group.save()

        # 更新权限
        if permissions_ids:
            permissions = Permission.objects.filter(id__in=permissions_ids)
            group.permissions.set(permissions)
            logger.info(f"Updated permissions for group: {group.name}, count: {len(permissions)}")
        else:
            # If no permissions selected, clear all permissions
            group.permissions.clear()
            logger.info(f"Cleared all permissions for group: {group.name}")

        logger.info(f"Group updated successfully: {group.name} (ID: {group.id})")

        # Create Django admin history record
        try:
            # Get updated permissions
            new_permissions = set(group.permissions.all())
            new_permissions_count = len(new_permissions)

            # Build change message
            changes = []

            # Record name changes
            if original_name != name:
                changes.append(f"Name: '{original_name}' → '{name}'")

            # Record permission change details
            if original_permissions != new_permissions:
                # Calculate added and removed permissions
                added_permissions = new_permissions - original_permissions
                removed_permissions = original_permissions - new_permissions

                # Record added permissions
                if added_permissions:
                    added_names = [perm.name for perm in added_permissions]
                    added_names.sort()  # Sort to maintain consistency
                    changes.append(_('Added permissions: [{}]').format(', '.join(added_names)))

                # Record removed permissions
                if removed_permissions:
                    removed_names = [perm.name for perm in removed_permissions]
                    removed_names.sort()  # Sort to maintain consistency
                    changes.append(_('Removed permissions: [{}]').format(', '.join(removed_names)))

                # Record permission count changes
                if original_permissions_count != new_permissions_count:
                    changes.append(_('Permissions count: {} → {}').format(original_permissions_count, new_permissions_count))

            change_message = _('Changed group via modal form.')
            if changes:
                change_message += f" {_('Changes')}: {'; '.join(changes)}"

            LogEntry.objects.create(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(Group).pk,
                object_id=group.pk,
                object_repr=str(group),
                action_flag=CHANGE,
                change_message=change_message
            )
            logger.info(f"Created admin log entry for group update: {group.name}")
        except Exception as log_error:
            logger.warning(f"Failed to create admin log entry for group {group.name}: {log_error}")

        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Group updated successfully'),
                'group': {
                    'id': group.id,
                    'name': group.name,
                    'permissions_count': group.permissions.count()
                }
            })

        # Otherwise redirect back to user group list page
        return HttpResponseRedirect(reverse('admin:auth_group_changelist'))

    except Exception as e:
        logger.error(f"Error editing group ID {group_id}: {str(e)}")
        logger.error(traceback.format_exc())

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('An error occurred while updating the group'),
                'error': str(e)
            }, status=500)

        # 重定向回用户组列表页面，并显示错误消息
        return HttpResponseRedirect(reverse('admin:auth_group_changelist'))