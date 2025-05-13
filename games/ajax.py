from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.translation import gettext as _

from .models import (
    Game, FrontUser, FrontGameFavorite, FrontGameHistory, FrontGameComment, UserProfile
)
from core.mail import send_verification_code
from core.api_utils import api_response

import logging
import re
import random
import string
from django.core.mail import send_mail
from django.utils import timezone
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json

logger = logging.getLogger(__name__)

@require_GET
def get_game_detail(request, game_id):
    """获取游戏详情的API"""
    try:
        game = get_object_or_404(Game, id=game_id)
        
        # 获取游戏评论
        comments = FrontGameComment.objects.filter(game=game, is_active=True)
        
        # 获取相关游戏
        related_games = Game.objects.filter(
            categories__in=game.categories.all()
        ).exclude(id=game.id).distinct()[:4]
        
        # 用户是否收藏
        is_favorite = False
        if request.user.is_authenticated and hasattr(request.user, 'is_member'):
            is_favorite = FrontGameFavorite.objects.filter(
                user=request.user, game=game
            ).exists()
        
        # 构建返回数据
        response_data = {
            'success': True,
            'game': {
                'id': game.id,
                'title': game.title,
                'slug': game.slug,
                'description': game.description,
                'thumbnail_url': game.thumbnail.url if game.thumbnail else None,
                'iframe_url': game.iframe_url,
                'rating': float(game.rating),
                'play_count': game.play_count,
                'created_at': game.created_at.strftime('%Y-%m-%d'),
                'categories': [
                    {'id': category.id, 'name': category.name, 'slug': category.slug}
                    for category in game.categories.all()
                ]
            },
            'comments': [
                {
                    'id': comment.id,
                    'user': {
                        'id': comment.user.id,
                        'username': comment.user.username,
                        'avatar_url': comment.user.avatar.url if comment.user.avatar else None
                    },
                    'rating': comment.rating,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
                }
                for comment in comments
            ],
            'related_games': [
                {
                    'id': related.id,
                    'title': related.title,
                    'slug': related.slug,
                    'thumbnail_url': related.thumbnail.url if related.thumbnail else None,
                    'rating': float(related.rating)
                }
                for related in related_games
            ],
            'is_favorite': is_favorite
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_POST
def favorite_toggle_api(request):
    """
    处理游戏收藏切换的新API - 无CSRF验证
    请求方式: POST
    请求参数: 
        - game_id: 游戏ID
    """
    # 检查用户是否已登录
    if not request.user.is_authenticated:
        return api_response(
            success=False,
            message="请先登录后再收藏游戏",
            code="login_required",
            redirect_url="/login/?next=" + request.META.get('HTTP_REFERER', '/')
        )
    
    try:
        # 从POST或JSON正文中获取game_id
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            game_id = data.get('game_id')
        else:
            game_id = request.POST.get('game_id')
        
        if not game_id:
            return api_response(
                success=False,
                message="缺少必要参数",
                code="invalid_params"
            )
        
        game = Game.objects.get(id=game_id)
        
        # 使用模型的toggle_favorite类方法切换收藏状态
        is_favorite = FrontGameFavorite.toggle_favorite(request.user, game)
        
        # 根据结果返回不同消息
        if is_favorite:
            message = f"已收藏《{game.title}》"
        else:
            message = f"已取消收藏《{game.title}》"
        
        return api_response(
            success=True,
            message=message,
            data={
                'game_id': game.id,
                'game_title': game.title,
                'is_favorite': is_favorite
            },
            code="success"
        )
    except Game.DoesNotExist:
        return api_response(
            success=False,
            message="游戏不存在",
            code="not_found"
        )
    except Exception as e:
        logger.error(f"收藏操作失败: {str(e)}")
        return api_response(
            success=False,
            message="收藏操作失败，请稍后再试",
            code="internal_error"
        )

@require_POST
def favorite_toggle(request, game_id=None):
    """
    处理游戏收藏切换的API - 有CSRF验证
    请求方式: POST
    请求参数: 
        - game_id: 游戏ID（可以从URL参数或请求体中获取）
    """
    # 检查用户是否已登录
    if not request.user.is_authenticated:
        return api_response(
            success=False,
            message="请先登录后再收藏游戏",
            code="login_required",
            redirect_url="/login/?next=" + request.META.get('HTTP_REFERER', '/')
        )
    
    try:
        # 优先使用URL路径中的game_id参数
        if game_id is None:
            # 从POST或JSON正文中获取game_id
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                game_id = data.get('game_id')
            else:
                game_id = request.POST.get('game_id')
        
        if not game_id:
            return api_response(
                success=False,
                message="缺少必要参数",
                code="invalid_params"
            )
        
        game = Game.objects.get(id=game_id)
        
        # 使用模型的toggle_favorite类方法切换收藏状态
        is_favorite = FrontGameFavorite.toggle_favorite(request.user, game)
        
        # 根据结果返回不同消息
        if is_favorite:
            message = f"已收藏《{game.title}》"
        else:
            message = f"已取消收藏《{game.title}》"
        
        return api_response(
            success=True,
            message=message,
            data={
                'game_id': game.id,
                'game_title': game.title,
                'is_favorite': is_favorite
            },
            code="success"
        )
    except Game.DoesNotExist:
        return api_response(
            success=False,
            message="游戏不存在",
            code="not_found"
        )
    except Exception as e:
        logger.error(f"收藏操作失败: {str(e)}")
        return api_response(
            success=False,
            message="收藏操作失败，请稍后再试",
            code="internal_error"
        )

@login_required
@require_POST
def comment_like(request, comment_id):
    """点赞评论的AJAX处理函数"""
    # 检查评论功能是否开启
    from admin_panel.models import ConfigSettings
    enable_comments = ConfigSettings.get_config('enable_comments', True)
    if not enable_comments:
        return JsonResponse({
            'success': False,
            'message': '评论功能已关闭',
            'code': 'comments_disabled'
        })
        
    comment = get_object_or_404(FrontGameComment, id=comment_id)
    user_id = request.user.id
    
    # 这里简化处理，实际中可能需要专门的点赞模型
    if hasattr(comment, 'likes'):
        likes = comment.likes or []
        
        if user_id in likes:
            likes.remove(user_id)
            liked = False
        else:
            likes.append(user_id)
            liked = True
        
        comment.likes = likes
        comment.save()
    else:
        comment.likes = [user_id]
        comment.save()
        liked = True
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': len(comment.likes) if hasattr(comment, 'likes') else 1
    })

@login_required
@require_POST
def comment_submit(request):
    """提交评论的AJAX处理函数"""
    try:
        # 检查评论功能是否开启
        from admin_panel.models import ConfigSettings
        enable_comments = ConfigSettings.get_config('enable_comments', True)
        if not enable_comments:
            return api_response(
                success=False,
                message='评论功能已关闭',
                code='comments_disabled'
            )
            
        user = request.user
        game_id = request.POST.get('game_id')
        content = request.POST.get('content')
        rating = request.POST.get('rating')
        parent_id = request.POST.get('parent_id')
        
        if not game_id or not content:
            return api_response(
                success=False,
                message='参数不完整，评论内容和游戏ID不能为空',
                code='bad_request'
            )
        
        game = get_object_or_404(Game, id=game_id)
        
        # 确保用户有资料
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # 创建评论
        comment = FrontGameComment.objects.create(
            user=user,
            game=game,
            content=content,
            rating=int(rating) if rating else 5
        )
        
        # 如果是回复其他评论
        if parent_id:
            try:
                parent_comment = FrontGameComment.objects.get(id=parent_id)
                comment.parent = parent_comment
                comment.save()
            except FrontGameComment.DoesNotExist:
                pass
                
        # 更新游戏的平均评分
        avg_rating = FrontGameComment.objects.filter(
            game=game, is_active=True
        ).aggregate(Avg('rating'))['rating__avg']
        
        game.rating = avg_rating if avg_rating else 0
        game.save(update_fields=['rating'])
        
        # 构建评论数据用于返回
        comment_data = {
            'id': comment.id,
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar_url': profile.avatar.url if profile.avatar else None,
            },
            'content': comment.content,
            'rating': comment.rating,
            'likes_count': len(comment.likes or []),
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_active': comment.is_active
        }
        
        return api_response(
            success=True,
            message='评论已成功提交',
            data={
                'comment': comment_data,
                'game_rating': float(game.rating)
            }
        )
    except Exception as e:
        logger.error(f"提交评论失败: {str(e)}")
        return api_response(
            success=False,
            message='提交评论时发生错误',
            code='internal_error'
        )

@login_required
@require_POST
def game_rating_submit(request, game_id):
    """提交游戏评分的AJAX处理函数"""
    rating = request.POST.get('rating')
    
    if not rating:
        return JsonResponse({
            'success': False,
            'error': '评分不能为空'
        }, status=400)
    
    game = get_object_or_404(Game, id=game_id)
    user = request.user
    
    # 查找或创建评论
    comment, created = FrontGameComment.objects.get_or_create(
        user=user,
        game=game,
        parent=None,
        defaults={'content': '给游戏评分', 'rating': rating}
    )
    
    if not created:
        comment.rating = rating
        comment.save()
    
    # 更新游戏平均评分
    avg_rating = FrontGameComment.objects.filter(game=game, parent=None).exclude(rating=0).aggregate(Avg('rating'))
    game.rating = avg_rating['rating__avg'] or 0
    game.save()
    
    return JsonResponse({
        'success': True,
        'rating': float(rating),
        'game_rating': game.rating
    })

@require_POST
def log_game_play(request, game_id):
    """记录游戏游玩的AJAX处理函数"""
    try:
        # 检查用户是否已登录，如果未登录返回JSON响应而不是重定向
        if not request.user.is_authenticated:
            return api_response(
                success=False,
                message="请先登录后再记录游戏数据",
                code="login_required"
            )
            
        user = request.user
        
        # 尝试从JSON数据中获取action
        try:
            data = json.loads(request.body)
            action = data.get('action')
        except (ValueError, TypeError):
            # 如果不是JSON格式，则从POST数据中获取
            action = request.POST.get('action')
        
        if action not in ['start', 'end']:
            return api_response(
                success=False,
                message='无效的操作',
                code='bad_request'
            )
        
        game = get_object_or_404(Game, id=game_id)
        
        # 确保用户有资料
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # 记录游戏历史
        history, created = FrontGameHistory.objects.get_or_create(
            user=user,
            game=game
        )
        
        if action == 'start':
            # 游戏开始时更新last_played
            history.save()  # 这会自动更新last_played
        elif action == 'end':
            # 游戏结束时增加play_count
            history.play_count += 1
            history.save()
            
            # 同时更新游戏的总游玩次数
            game.play_count += 1
            game.save()
        
        return api_response(
            success=True,
            message=f"游戏{action}记录成功",
            data={
                'game_id': game.id,
                'play_count': history.play_count,
                'last_played': history.last_played.strftime('%Y-%m-%d %H:%M:%S'),
                'action': action
            }
        )
    except Exception as e:
        logger.error(f"记录游戏游玩时发生错误: {str(e)}")
        return api_response(
            success=False,
            message="记录游戏游玩失败",
            code="internal_error"
        )

@require_POST
def send_password_reset_code(request):
    """发送密码重置验证码的AJAX处理函数"""
    try:
        from django.contrib.auth.models import User
        import json
        
        # 获取请求数据，支持表单数据和JSON格式
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                email = data.get('email', '').strip()
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'errors': {'general': ['无效的JSON格式']},
                    'message': '无效的请求格式'
                }, status=400)
        else:
            email = request.POST.get('email', '').strip()
        
        # 记录接收到的请求
        logger.debug(f"接收到发送密码重置验证码请求: email={email}")
        
        # 基本验证
        if not email:
            return JsonResponse({
                'success': False,
                'errors': {'email': ['邮箱地址不能为空']}
            })
            
        # 邮箱格式验证
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return JsonResponse({
                'success': False,
                'errors': {'email': ['请输入有效的邮箱地址']}
            })
            
        # 检查邮箱是否存在
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"尝试重置密码的邮箱不存在: {email}")
            # 明确告诉用户邮箱不存在
            return JsonResponse({
                'success': False,
                'errors': {'email': ['该邮箱未注册，请检查您的输入或注册新账号']},
                'message': '该邮箱未注册，请检查您的输入或注册新账号'
            })
            
        # 生成6位数字验证码
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # 存储验证码到缓存，设置10分钟过期
        cache_key = f"password_reset_code_{email}"
        cache.set(cache_key, verification_code, 60 * 10)  # 10分钟过期
        
        # 使用core.mail模块发送验证码
        try:
            # 使用新的验证码发送功能
            send_success = send_verification_code(
                email=email,
                code=verification_code,
                fail_silently=False
            )
            
            if send_success:
                logger.info(f"密码重置验证码已发送: email={email}")
                return JsonResponse({
                    'success': True,
                    'message': '验证码已发送到您的邮箱，请查收'
                })
            else:
                logger.error(f"发送密码重置邮件失败")
                return JsonResponse({
                    'success': False,
                    'errors': {'general': ['发送验证码失败，请稍后重试']}
                })
        except Exception as e:
            logger.error(f"发送密码重置邮件失败: {str(e)}")
            return JsonResponse({
                'success': False,
                'errors': {'general': ['发送验证码失败，请稍后重试']}
            })
            
    except Exception as e:
        logger.error(f"发送验证码过程中发生错误: {str(e)}")
        return JsonResponse({
            'success': False, 
            'errors': {'general': ['服务器错误，请稍后重试']}
        }, status=500)

@require_POST
def verify_reset_code(request):
    """验证密码重置验证码的AJAX处理函数"""
    try:
        email = request.POST.get('email', '').strip()
        code = request.POST.get('code', '').strip()
        
        logger.debug(f"接收到验证密码重置码请求: email={email}, code=****")
        
        # 基本验证
        if not email or not code:
            return JsonResponse({
                'success': False,
                'errors': {'general': ['邮箱和验证码不能为空']}
            })
            
        # 从缓存获取验证码
        cache_key = f"password_reset_code_{email}"
        stored_code = cache.get(cache_key)
        
        if not stored_code:
            logger.warning(f"验证码不存在或已过期: email={email}")
            return JsonResponse({
                'success': False,
                'errors': {'code': ['验证码已过期，请重新获取']}
            })
            
        # 验证码比对
        if stored_code != code:
            logger.warning(f"验证码不匹配: email={email}")
            return JsonResponse({
                'success': False,
                'errors': {'code': ['验证码不正确']}
            })
            
        # 验证成功，生成重置令牌
        reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        # 存储令牌到缓存，设置30分钟过期
        token_key = f"password_reset_token_{email}"
        cache.set(token_key, reset_token, 60 * 30)  # 30分钟过期
        
        # 清除验证码
        cache.delete(cache_key)
        
        logger.info(f"验证码验证成功，生成重置令牌: email={email}")
        
        return JsonResponse({
            'success': True,
            'token': reset_token,
            'email': email,
            'message': '验证成功'
        })
        
    except Exception as e:
        logger.error(f"验证重置码过程中发生错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': ['服务器错误，请稍后重试']}
        }, status=500)

@require_POST
def reset_password(request):
    """重置密码的AJAX处理函数"""
    try:
        from django.contrib.auth.models import User
        import json
        
        # 获取请求数据，支持表单数据和JSON格式
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                email = data.get('email', '').strip()
                token = data.get('token', '').strip()
                new_password = data.get('new_password', '')
                confirm_password = data.get('confirm_password', '')
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'errors': {'general': ['无效的JSON格式']},
                    'message': '无效的请求格式'
                }, status=400)
        else:
            email = request.POST.get('email', '').strip()
            token = request.POST.get('token', '').strip()
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
        
        logger.debug(f"接收到重置密码请求: email={email}, token=****")
        
        # 基本验证
        if not all([email, token, new_password, confirm_password]):
            return JsonResponse({
                'success': False,
                'errors': {'general': ['所有字段都是必填的']}
            })
            
        # 密码一致性验证
        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'errors': {'confirm_password': ['两次输入的密码不匹配']}
            })
            
        # 密码强度验证
        if len(new_password) < 8:
            return JsonResponse({
                'success': False,
                'errors': {'new_password': ['密码至少需要8个字符']}
            })
        if new_password.isdigit():
            return JsonResponse({
                'success': False,
                'errors': {'new_password': ['密码不能是纯数字']}
            })
            
        # 验证令牌
        token_key = f"password_reset_token_{email}"
        stored_token = cache.get(token_key)
        
        if not stored_token or stored_token != token:
            logger.warning(f"密码重置令牌无效: email={email}")
            return JsonResponse({
                'success': False,
                'errors': {'general': ['重置链接已过期或无效，请重新开始密码重置流程']},
                'message': '重置链接已过期或无效，请重新开始密码重置流程'
            })
            
        # 获取用户
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.error(f"尝试重置密码的用户不存在: email={email}")
            return JsonResponse({
                'success': False,
                'errors': {'general': ['用户不存在，请检查您的邮箱']},
                'message': '用户不存在，请检查您的邮箱'
            })
            
        # 设置新密码
        user.set_password(new_password)
        user.save()
        
        # 清除令牌
        cache.delete(token_key)
        
        logger.info(f"用户密码重置成功: email={email}, user_id={user.id}")
        
        return JsonResponse({
            'success': True,
            'message': '密码重置成功，请使用新密码登录',
            'redirect': '/login/'
        })
        
    except Exception as e:
        logger.error(f"重置密码过程中发生错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': ['服务器错误，请稍后重试']},
            'message': '重置密码失败，请稍后重试'
        }, status=500)

@require_POST
def login_ajax(request):
    """
    使用自定义认证后端的异步登录API接口
    支持邮箱或用户名登录
    请求格式：JSON {username: 用户名或邮箱, password: 密码, remember_me: 是否记住我}
    响应格式：JSON {success: 布尔值, redirect: 跳转URL, errors: 错误信息}
    """
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'errors': {'general': '不支持的请求方法'}}, status=405)
    
    try:
        # 解析JSON数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试从POST中获取数据
            data = request.POST
            
        username = data.get('username', '')
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        next_url = data.get('next', '')
        
        # 验证输入
        errors = {}
        if not username:
            errors['username'] = '请输入邮箱或用户名'
        if not password:
            errors['password'] = '请输入密码'
            
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        # 记录登录尝试信息和会话状态
        logger.info(f"登录尝试: username={username}, remember_me={remember_me}")
        logger.debug(f"请求会话状态: session_key={request.session.session_key}, engine={request.session.__class__.__name__}")
        
        # 使用Django的authenticate函数进行认证
        # 会自动使用settings.py中配置的认证后端，包括我们自定义的支持邮箱登录的后端
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 登录用户
            login(request, user)
            logger.info(f"用户登录成功: user_id={user.id}, username={user.username}")
            
            # 确保用户有资料
            UserProfile.objects.get_or_create(user=user)
            
            # 设置会话过期时间
            if not remember_me:
                # 浏览器关闭时过期
                request.session.set_expiry(0)
            
            # 获取重定向URL
            redirect_url = next_url if next_url else reverse('games:home')
            
            return JsonResponse({
                'success': True,
                'redirect': redirect_url
            })
        else:
            logger.warning(f"用户登录失败: username={username}")
            return JsonResponse({
                'success': False,
                'errors': {
                    'general': '邮箱/用户名或密码错误'
                }
            }, status=401)
            
    except Exception as e:
        import traceback
        logger.error(f"登录过程中发生错误: {str(e)}\n{traceback.format_exc()}")
        
        return JsonResponse({
            'success': False,
            'errors': {
                'general': '登录过程中发生错误，请稍后再试'
            }
        }, status=500)

@require_GET
def game_history_ajax(request):
    """用户游戏历史记录的AJAX请求处理"""
    if not request.user.is_authenticated:
        return api_response(
            success=False,
            message="请先登录后查看游戏历史",
            code="login_required"
        )
    
    try:
        # 获取查询参数
        search = request.GET.get('search', '')
        category = request.GET.get('category', '')
        sort = request.GET.get('sort', '-last_played')
        page = int(request.GET.get('page', 1))
        per_page = 12  # 每页显示12个游戏
        
        # 获取用户的游戏历史
        query = FrontGameHistory.objects.filter(user=request.user)
        
        # 应用搜索过滤
        if search:
            query = query.filter(game__title__icontains=search)
        
        # 应用分类过滤
        if category and category != 'all':
            query = query.filter(game__categories__slug=category)
        
        # 应用排序
        if sort == 'last_played':
            query = query.order_by('last_played')
        elif sort == '-last_played':
            query = query.order_by('-last_played')
        elif sort == 'play_count':
            query = query.order_by('play_count')
        elif sort == '-play_count':
            query = query.order_by('-play_count')
        elif sort == 'title':
            query = query.order_by('game__title')
        elif sort == '-title':
            query = query.order_by('-game__title')
        else:
            query = query.order_by('-last_played')  # 默认按最近游玩时间排序
        
        # 计算分页
        total_count = query.count()
        start_index = (page - 1) * per_page
        end_index = page * per_page
        
        history_items = query[start_index:end_index]
        has_more = total_count > page * per_page
        
        # 构建响应数据
        history_list = []
        for history in history_items:
            game = history.game
            history_list.append({
                'id': history.id,
                'game_id': game.id,
                'title': game.title,
                'slug': game.slug,
                'thumbnail': game.thumbnail.url if game.thumbnail else '',
                'category': game.category.name if game.category else '未分类',
                'rating': game.rating,
                'play_count': history.play_count,
                'last_played': history.last_played.strftime('%Y-%m-%d %H:%M'),
                'url': game.get_absolute_url()
            })
        
        return api_response(
            success=True,
            message="成功获取游戏历史",
            data={
                'history': history_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'has_more': has_more
                },
                'filters': {
                    'search': search,
                    'category': category,
                    'sort': sort
                }
            },
            code="success"
        )
    except Exception as e:
        logger.error(f"获取游戏历史失败: {str(e)}")
        return api_response(
            success=False,
            message="获取游戏历史失败，请稍后再试",
            code="internal_error"
        )

@require_POST
def delete_history_ajax(request):
    """删除单条游戏历史记录的AJAX请求处理"""
    if not request.user.is_authenticated:
        return api_response(
            success=False,
            message="请先登录后操作",
            code="login_required"
        )
    
    try:
        history_id = request.POST.get('history_id')
        
        # 查找记录并验证所有权
        history = get_object_or_404(FrontGameHistory, id=history_id, user=request.user)
        game_title = history.game.title
        
        # 删除记录
        history.delete()
        
        return api_response(
            success=True,
            message=f"已删除《{game_title}》的游戏记录",
            data={
                'deleted_id': history_id,
                'game_title': game_title
            },
            code="success"
        )
    except FrontGameHistory.DoesNotExist:
        return api_response(
            success=False,
            message="找不到该游戏记录",
            code="not_found"
        )
    except Exception as e:
        logger.error(f"删除游戏历史记录失败: {str(e)}")
        return api_response(
            success=False,
            message="删除游戏历史记录失败，请稍后再试",
            code="internal_error"
        )

@require_POST
def clear_history_ajax(request):
    """清空所有游戏历史记录的AJAX处理函数"""
    # 验证用户是否登录
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': '请先登录',
            'code': 'unauthenticated',
            'redirect_url': '/accounts/login/?next=/profile/history/'
        }, status=401)
    
    user = request.user
    
    try:
        # 删除该用户的所有历史记录
        deleted_count = FrontGameHistory.objects.filter(user=user).delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'已清空{deleted_count}条历史记录'
        })
    except Exception as e:
        logger.error(f"清空游戏历史记录失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': '操作失败，请稍后再试',
            'error': str(e)
        }, status=500)

@require_POST
def clear_all_history_ajax(request):
    """清空用户所有游戏历史记录的AJAX请求处理"""
    if not request.user.is_authenticated:
        return api_response(
            success=False,
            message="请先登录后操作",
            code="login_required"
        )
    
    try:
        # 删除该用户的所有历史记录
        deleted_count, _ = FrontGameHistory.objects.filter(user=request.user).delete()
        
        return api_response(
            success=True,
            message=f"已清空{deleted_count}条游戏历史记录",
            data={
                'deleted_count': deleted_count
            },
            code="success"
        )
    except Exception as e:
        logger.error(f"清空游戏历史记录失败: {str(e)}")
        return api_response(
            success=False,
            message="清空游戏历史记录失败，请稍后再试",
            code="internal_error"
        )

@require_GET
def get_game_comments(request, game_id):
    """获取游戏评论列表的API"""
    try:
        # 检查评论功能是否开启
        from admin_panel.models import ConfigSettings
        enable_comments = ConfigSettings.get_config('enable_comments', True)
        if not enable_comments:
            # 评论功能关闭时，返回空列表而不是错误，前端可以显示相应提示
            return api_response(
                success=True,
                data={
                    'comments': [],
                    'has_next': False,
                    'has_previous': False,
                    'current_page': 1,
                    'total_pages': 0,
                    'next_page': None,
                    'previous_page': None,
                    'total_comments': 0,
                    'per_page': 10,
                    'comments_disabled': True  # 添加标志表示评论已禁用
                },
                message="评论功能已关闭"
            )
        
        # 直接使用game_id，避免不必要的JOIN查询
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        
        # 限制每页条数，防止过大请求
        if per_page > 20:
            per_page = 20
        
        # 构建查询 - 只选择需要的字段
        comments_query = FrontGameComment.objects.filter(
            game_id=game_id,  # 使用game_id而不是game对象，减少JOIN
            is_active=True, 
            parent__isnull=True  # 只获取顶级评论，不获取回复
        ).select_related(
            'user'  # 预加载用户信息
        ).only(
            'id', 'user_id', 'content', 'rating', 'created_at', 'likes',
            'user__username'  # 确保预加载用户名
        ).order_by('-created_at')
        
        # 获取评论总数（用于分页计算）
        total_count = comments_query.count()
        
        # 在数据库层面进行分页 - 使用Django的Paginator
        paginator = Paginator(comments_query, per_page)
        try:
            current_page = paginator.page(page)
        except PageNotAnInteger:
            current_page = paginator.page(1)
        except EmptyPage:
            # 如果请求的页面超出范围，返回最后一页
            current_page = paginator.page(paginator.num_pages)
        
        # 获取此页的实际记录
        comments = list(current_page.object_list)
        
        # 一次性获取所有相关用户的资料，避免循环查询
        user_ids = [comment.user_id for comment in comments]
        
        # 优化：使用values查询直接获取需要的用户资料字段
        user_profiles = UserProfile.objects.filter(
            user_id__in=user_ids
        ).values('user_id', 'avatar')
        
        # 将用户资料转换为字典，方便快速查找
        user_profile_dict = {profile['user_id']: profile for profile in user_profiles}
        
        # 格式化评论数据
        comment_list = []
        for comment in comments:
            # 从字典中获取用户资料，避免每次循环都查询数据库
            profile = user_profile_dict.get(comment.user_id, {})
            avatar_url = profile.get('avatar', None)
            
            comment_data = {
                'id': comment.id,
                'user': {
                    'id': comment.user_id,
                    'username': comment.user.username,
                    'avatar_url': avatar_url if avatar_url else None
                },
                'rating': comment.rating,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # 时间格式精确到秒
                'likes_count': len(comment.likes or [])
            }
            comment_list.append(comment_data)
        
        # 构建响应数据
        response_data = {
            'comments': comment_list,
            'has_next': current_page.has_next(),
            'has_previous': current_page.has_previous(),
            'current_page': page,
            'total_pages': paginator.num_pages,
            'next_page': current_page.next_page_number() if current_page.has_next() else None,
            'previous_page': current_page.previous_page_number() if current_page.has_previous() else None,
            'total_comments': total_count,
            'per_page': per_page
        }
        
        return api_response(
            success=True,
            data=response_data,
            message="评论加载成功"
        )
    except Exception as e:
        logger.error(f"获取评论失败: {str(e)}")
        return api_response(
            success=False,
            message=f"获取评论失败: {str(e)}",
            code='comment_fetch_error'
        )