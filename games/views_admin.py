from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Game
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