from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View, TemplateView, FormView, RedirectView
from django.views.generic.edit import FormView
from django.db.models import Q, Avg, Count, F, Value, ExpressionWrapper, FloatField, Sum
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.http import JsonResponse, Http404, HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth import views as auth_views, login as auth_login, logout, update_session_auth_hash
from django.contrib import messages
from datetime import datetime, timedelta, timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging
import math
from django.template.loader import render_to_string
from django.contrib.auth.views import LoginView
import random
import string
from django.core.mail import send_mail
from django.core.cache import cache
from core.api_utils import api_response
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from django.utils.http import url_has_allowed_host_and_scheme

from .models import (
    Game,
    GameCategory,
    FrontUser,
    FrontGameFavorite,
    FrontGameHistory,
    FrontGameComment,
    MembershipFeature,
    GameTag,
    UserProfile)
from .forms import UserRegistrationForm, LoginForm
from admin_panel.models import ConfigSettings

# 获取logger
logger = logging.getLogger(__name__)


class GameShopView(View):
    """游戏商城视图"""

    def get(self, request):
        # 获取热门付费游戏
        popular_paid_games = Game.objects.filter(
            status='online',
            has_in_app_purchases=True
        ).order_by('-play_count')[:8]

        # 获取最新付费游戏
        new_paid_games = Game.objects.filter(
            status='online',
            has_in_app_purchases=True
        ).order_by('-created_at')[:8]

        # 获取折扣游戏（假设有discount字段，如果没有可以调整）
        discounted_games = Game.objects.filter(
            status='online',
            has_in_app_purchases=True,
            is_discounted=True
        ).order_by('-discount_rate')[:4]

        # 获取游戏分类（付费游戏相关分类）
        categories = GameCategory.objects.filter(is_active=True)

        # 判断用户是否已登录
        is_logged_in = request.user.is_authenticated
        user_membership_type = None

        # 获取用户会员信息（如果已登录）
        if is_logged_in and hasattr(request.user, 'is_member'):
            try:
                front_user = FrontUser.objects.get(
                    username=request.user.username)
                user_membership_type = front_user.membership_type
            except FrontUser.DoesNotExist:
                pass

        context = {
            'popular_paid_games': popular_paid_games,
            'new_paid_games': new_paid_games,
            'discounted_games': discounted_games,
            'categories': categories,
            'is_logged_in': is_logged_in,
            'user_membership_type': user_membership_type,
            'section': 'shop'
        }

        return render(request, 'games/game_shop.html', context)


class HomeView(View):
    """网站首页视图"""

    def get(self, request):
        # 获取热门游戏 - 仅限首页展示四个游戏卡片，热门游戏页面不受影响
        popular_games = Game.objects.filter(
            status='online').order_by('-play_count')[:4]

        # 获取最新上线游戏 - 仅限首页展示四个游戏卡片，最新游戏页面不受影响
        new_games = Game.objects.filter(
            status='online').order_by('-created_at')[:4]

        # 获取所有游戏分类
        categories = GameCategory.objects.filter(is_active=True, parent=None)

        # 使用推荐算法获取推荐游戏
        recommended_games = self.get_recommended_games(request)

        context = {
            'popular_games': popular_games,
            'new_games': new_games,
            'recommended_games': recommended_games,
            'categories': categories,
        }
        return render(request, 'games/home.html', context)

    def get_recommended_games(self, request):
        """
        推荐算法：综合考虑游玩次数和评分，计算一个推荐分数
        - 评分权重: 60%
        - 游玩次数权重: 40%
        """
        from django.db.models import FloatField, ExpressionWrapper, Value

        # 获取基础查询集 - 仅在线游戏
        base_queryset = Game.objects.filter(status='online')

        # 获取最高的评分和游玩次数，用于归一化
        max_rating = base_queryset.order_by('-rating').first()
        max_rating = float(max_rating.rating) if max_rating else 5.0
        max_rating = max(max_rating, 0.1)  # 防止除以0

        max_play_count = base_queryset.order_by('-play_count').first()
        max_play_count = max_play_count.play_count if max_play_count else 1
        max_play_count = max(max_play_count, 1)  # 防止除以0

        # 用户个性化推荐 - 如果用户已登录，考虑用户历史记录
        if request.user.is_authenticated and hasattr(
                request.user, 'game_history'):
            # 尝试获取用户的游戏历史
            try:
                # 获取用户最近玩过的游戏的分类
                user_history = FrontGameHistory.objects.filter(
                    user=request.user
                ).select_related('game').order_by('-last_played')[:5]

                # 如果用户有历史记录，优先考虑用户喜好的分类
                if user_history.exists():
                    # 获取用户最近玩过的游戏的分类ID
                    user_game_ids = [
                        history.game.id for history in user_history]
                    user_categories = GameCategory.objects.filter(
                        games__in=user_game_ids
                    ).distinct()

                    if user_categories.exists():
                        # 为用户喜欢的分类的游戏加权
                        user_category_ids = [cat.id for cat in user_categories]
                        user_preference_games = base_queryset.filter(
                            categories__id__in=user_category_ids
                        ).exclude(
                            id__in=user_game_ids  # 排除用户已经玩过的游戏
                        ).distinct()

                        # 计算评分归一化表达式
                        rating_expr = ExpressionWrapper(
                            F('rating') / Value(max_rating),
                            output_field=FloatField()
                        )

                        # 计算游玩次数归一化表达式
                        play_count_expr = ExpressionWrapper(
                            F('play_count') / Value(max_play_count),
                            output_field=FloatField()
                        )

                        # 计算组合得分表达式
                        score_expr = ExpressionWrapper(
                            (rating_expr * Value(0.6)) + (play_count_expr * Value(0.4)),
                            output_field=FloatField()
                        )

                        # 应用评分和游玩次数加权算法
                        annotated_games = user_preference_games.annotate(
                            rating_normalized=rating_expr,
                            play_count_normalized=play_count_expr,
                            recommendation_score=score_expr
                        ).order_by('-recommendation_score')[:4]

                        if annotated_games.exists():
                            return annotated_games
            except Exception as e:
                logger.error(f"用户推荐出错: {str(e)}")

        # 通用推荐（用户未登录或没有历史记录）
        # 计算评分归一化表达式
        rating_expr = ExpressionWrapper(
            F('rating') / Value(max_rating),
            output_field=FloatField()
        )

        # 计算游玩次数归一化表达式
        play_count_expr = ExpressionWrapper(
            F('play_count') / Value(max_play_count),
            output_field=FloatField()
        )

        # 计算组合得分表达式
        score_expr = ExpressionWrapper(
            (rating_expr * Value(0.6)) + (play_count_expr * Value(0.4)),
            output_field=FloatField()
        )

        return base_queryset.annotate(
            rating_normalized=rating_expr,
            play_count_normalized=play_count_expr,
            recommendation_score=score_expr
        ).order_by('-recommendation_score')[:4]


class GameListView(ListView):
    """游戏列表视图"""
    model = Game
    template_name = 'games/game_categories.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_paginate_by(self, queryset):
        """自定义分页数量"""
        # 获取每页显示数量参数，默认为12
        per_page = self.request.GET.get('per_page')
        if per_page:
            try:
                # 限制每页显示数量在合理范围内
                per_page = int(per_page)
                if per_page in [12, 24, 36]:
                    return per_page
            except ValueError:
                pass
        return self.paginate_by  # 返回默认值

    def get_queryset(self):
        queryset = Game.objects.filter(status='online')

        # 分类筛选 - 支持URL路径参数和GET参数
        category_slug = self.kwargs.get('category_slug')
        if not category_slug:
            # 尝试从GET参数获取分类
            category_slug = self.request.GET.get('category')

        if category_slug:
            try:
                category = get_object_or_404(GameCategory, slug=category_slug)
                # 获取当前分类及其所有子分类
                if category.children.exists():
                    categories = [category.id] + \
                        list(category.children.values_list('id', flat=True))
                    queryset = queryset.filter(
                        categories__id__in=categories).distinct()
                else:
                    queryset = queryset.filter(categories=category)
            except Http404:
                # 如果分类不存在，忽略筛选条件
                pass

        # 搜索功能
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            ).distinct()

        # 评分筛选
        rating_filter = self.request.GET.getlist('rating')
        if rating_filter:
            q_objects = Q()
            for rating in rating_filter:
                try:
                    rating_value = int(rating)
                    if rating_value == 5:
                        q_objects |= Q(rating__gte=5)
                    elif rating_value == 4:
                        q_objects |= Q(rating__gte=4, rating__lt=5)
                    elif rating_value == 3:
                        q_objects |= Q(rating__gte=3, rating__lt=4)
                except ValueError:
                    pass
            if q_objects:
                queryset = queryset.filter(q_objects)

        # 时间筛选
        time_filter = self.request.GET.get('time')
        if time_filter and time_filter != 'all':
            now = datetime.now()
            if time_filter == 'today':
                # 今天上线的游戏 - 从当天0点开始
                date_threshold = now.replace(
                    hour=0, minute=0, second=0, microsecond=0)
                queryset = queryset.filter(created_at__gte=date_threshold)
            elif time_filter == 'week':
                date_threshold = now - timedelta(days=7)
                queryset = queryset.filter(created_at__gte=date_threshold)
            elif time_filter == 'month':
                date_threshold = now - timedelta(days=30)
                queryset = queryset.filter(created_at__gte=date_threshold)
            elif time_filter == 'year':
                date_threshold = now - timedelta(days=365)
                queryset = queryset.filter(created_at__gte=date_threshold)

        # 特性筛选
        feature_filter = self.request.GET.getlist('feature')
        if feature_filter:
            q_objects = Q()
            for feature in feature_filter:
                if feature == 'multiplayer':
                    q_objects |= Q(is_multiplayer=True)
                elif feature == 'singleplayer':
                    q_objects |= Q(is_multiplayer=False)
                elif feature == 'touch':
                    q_objects |= Q(is_touch_optimized=True)
                elif feature == 'payment':
                    q_objects |= Q(has_in_app_purchases=True)
            if q_objects:
                queryset = queryset.filter(q_objects)

        # 排序
        sort_by = self.request.GET.get('sort')
        if sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-rating')
        elif sort_by == 'name':
            queryset = queryset.order_by('title')
        else:  # 默认按照流行度（播放次数）排序
            queryset = queryset.order_by('-play_count')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 获取所有分类
        all_categories = GameCategory.objects.filter(is_active=True)
        context['all_categories'] = all_categories

        # 当前分类 - 支持URL路径参数和GET参数
        category_slug = self.kwargs.get('category_slug')
        if not category_slug:
            # 尝试从GET参数获取分类
            category_slug = self.request.GET.get('category')

        if category_slug:
            try:
                context['current_category'] = get_object_or_404(
                    GameCategory, slug=category_slug)
            except Http404:
                # 如果分类不存在，不设置current_category
                pass

        # 搜索关键词
        search_query = self.request.GET.get('q')
        if search_query:
            context['search_query'] = search_query

        # 为分页器添加计数
        if hasattr(
                context,
                'paginator') and hasattr(
                context['paginator'],
                'count'):
            context['game_count'] = context['paginator'].count

        # 添加每页显示数量
        context['per_page'] = self.request.GET.get(
            'per_page', self.paginate_by)

        return context

    def get(self, request, *args, **kwargs):
        """重写get方法，支持AJAX请求"""
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        # 判断是否为AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # 渲染游戏列表片段
            html = render_to_string(
                'games/includes/game_list_fragment.html',
                context,
                request=request)
            return JsonResponse({
                'html': html,
                'success': True
            })

        # 常规请求返回完整页面
        return self.render_to_response(context)


class GameDetailView(DetailView):
    """游戏详情视图"""
    model = Game
    template_name = 'games/game_detail.html'
    context_object_name = 'game'
    slug_url_kwarg = 'game_slug'

    def get_queryset(self):
        # 使用core.models.Game中的status字段
        return Game.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.get_object()

        # 获取相关游戏
        # 使用Q对象进行或条件查询
        from django.db.models import Q, Count

        # 基础查询集
        related_query = Game.objects.filter(
            status='online').exclude(
            id=game.id)

        # 基于分类的推荐
        category_games = []
        if game.categories.exists():
            category_games = list(related_query.filter(
                categories__in=game.categories.all()
            ).distinct().annotate(
                match_type=Count('id')  # 用于排序
            ).order_by('-match_type', '-rating')[:4])

            # 添加匹配原因
            for g in category_games:
                g.match_reason = 'category'

        # 基于标签的推荐
        tag_games = []
        if hasattr(game, 'tags') and game.tags.exists():
            tag_games = list(related_query.filter(
                tags__in=game.tags.all()
            ).exclude(
                id__in=[g.id for g in category_games]
            ).distinct().annotate(
                match_type=Count('id')
            ).order_by('-match_type', '-rating')[:4])

            # 添加匹配原因
            for g in tag_games:
                g.match_reason = 'tag'

        # 基于高评分的推荐
        rating_games = []
        if len(category_games) + len(tag_games) < 6:
            # 获取评分接近或更高的游戏
            rating_threshold = max(
                3.5,
                float(
                    game.rating) -
                0.5)  # 至少3.5星或比当前游戏低0.5星

            rating_games = list(related_query.filter(
                rating__gte=rating_threshold
            ).exclude(
                id__in=[g.id for g in category_games + tag_games]
            ).order_by('-rating', '-play_count')[:6 - len(category_games) - len(tag_games)])

            # 添加匹配原因
            for g in rating_games:
                g.match_reason = 'rating'

        # 合并推荐结果，优先顺序：分类 > 标签 > 评分
        related_games = category_games + tag_games + rating_games
        context['related_games'] = related_games[:6]  # 最多显示6个推荐

        # 获取游戏评论数量 - 用于前端显示，不加载实际评论内容
        comment_count = FrontGameComment.objects.filter(
            game=game,
            parent__isnull=True,
            is_active=True
        ).count()
        
        # 获取当前用户是否收藏
        is_favorite = False
        user_played = False
        user_rating = None

        if self.request.user.is_authenticated:
            # 如果用户登录了，检查收藏状态和其他数据
            user = self.request.user
            profile, created = UserProfile.objects.get_or_create(user=user)

            # 检查是否收藏
            is_favorite = FrontGameFavorite.objects.filter(
                user=user,
                game=game
            ).exists()

            # 检查用户是否玩过这个游戏
            try:
                history = FrontGameHistory.objects.get(user=user, game=game)
                user_played = True
            except FrontGameHistory.DoesNotExist:
                user_played = False

            # 获取用户的评分，如果有的话
            try:
                user_comment = FrontGameComment.objects.filter(
                    user=user,
                    game=game,
                    parent__isnull=True  # 只获取顶级评论，不是回复
                ).first()
                if user_comment:
                    user_rating = user_comment.rating
            except Exception:
                user_rating = None

        # 将评论相关数据添加到上下文
        context['comment_count'] = comment_count
        
        # 其他数据
        context['is_favorite'] = is_favorite
        context['user_played'] = user_played
        context['user_rating'] = user_rating
        
        # 获取评论功能开关状态
        context['enable_comments'] = ConfigSettings.get_config('enable_comments', True)
        
        return context


@method_decorator(login_required, name='dispatch')
class UserProfileView(View):
    """用户个人中心"""

    def get(self, request):
        try:
            # 获取是否显示会员内容的配置
            show_member_content = ConfigSettings.get_config('show_member_content', True)
            if isinstance(show_member_content, str):
                show_member_content = show_member_content.lower() not in ('false', '0')
            
            # 获取用户资料
            profile, created = UserProfile.objects.get_or_create(
                user=request.user)

            # 获取收藏游戏
            favorites_query = FrontGameFavorite.objects.filter(
                user=request.user).select_related('game')

            # 获取游戏历史
            history = FrontGameHistory.objects.filter(
                user=request.user).select_related('game')

            # 处理搜索查询
            search_query = request.GET.get('search', '')
            if search_query:
                favorites_query = favorites_query.filter(
                    Q(game__title__icontains=search_query) |
                    Q(game__description__icontains=search_query)
                ).distinct()

            # 处理分类筛选
            category_id = request.GET.get('category', '')
            if category_id and category_id.isdigit():
                favorites_query = favorites_query.filter(
                    game__categories__id=int(category_id)).distinct()

            # 设置排序
            sort_by = request.GET.get('sort', 'recent')
            if sort_by == 'recent':
                favorites_query = favorites_query.order_by('-id')  # 默认按收藏时间倒序
            elif sort_by == 'name':
                favorites_query = favorites_query.order_by(
                    'game__title')  # 按游戏名称升序
            elif sort_by == 'rating':
                favorites_query = favorites_query.order_by(
                    '-game__rating')  # 按评分降序

            # 获取所有游戏分类，用于筛选下拉菜单
            categories = GameCategory.objects.filter(
                is_active=True).order_by('name')

            # 分页处理
            page = request.GET.get('page', 1)
            per_page = request.GET.get('per_page', 12)  # 默认每页12个游戏

            try:
                page = int(page)
                per_page = int(per_page)
                if per_page not in [12, 24, 36, 48]:  # 限制每页显示数量选项
                    per_page = 12
            except (ValueError, TypeError):
                page = 1
                per_page = 12

            # 使用正确的per_page值创建分页器
            paginator = Paginator(favorites_query, per_page)

            try:
                favorites_page = paginator.page(page)
            except PageNotAnInteger:
                favorites_page = paginator.page(1)
            except EmptyPage:
                # 如果请求的页面超出范围，返回最后一页
                favorites_page = paginator.page(paginator.num_pages)

            context = {
                'favorites': favorites_page,
                'history': history,
                'profile': profile,  # 传递用户资料对象到模板
                'user': request.user,  # 传递用户对象到模板
                'categories': categories,  # 添加分类数据
                'search_query': search_query,  # 添加搜索词，用于填充搜索框
                'selected_category': category_id,  # 添加选中的分类ID
                'current_sort': sort_by,  # 当前排序方式
                'per_page': per_page,  # 每页显示数量
                'is_paginated': paginator.num_pages > 1,  # 是否需要分页
                'page_obj': favorites_page,  # 分页对象
                'show_member_content': show_member_content,  # 添加会员内容显示配置
            }

            # 判断是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                try:
                    # 构建分页信息对象，用于异步加载
                    pagination_info = {
                        'current_page': favorites_page.number,
                        'num_pages': paginator.num_pages,
                        'has_next': favorites_page.has_next(),
                        'has_previous': favorites_page.has_previous(),
                        'next_page_number': favorites_page.next_page_number() if favorites_page.has_next() else None,
                        'previous_page_number': favorites_page.previous_page_number() if favorites_page.has_previous() else None,
                        'start_index': favorites_page.start_index(),
                        'end_index': favorites_page.end_index(),
                        'per_page': per_page,
                        'total_items': paginator.count,
                    }

                    # 确保传递所有必要的分页信息到模板
                    pagination_context = {
                        'is_paginated': paginator.num_pages > 1,
                        'page_obj': favorites_page,
                        'paginator': paginator,
                        'total_count': paginator.count,
                    }

                    # 只返回游戏列表部分的HTML和分页信息
                    html = render_to_string(
                        'games/includes/profile_games_list.html', context, request=request)
                    pagination_html = render_to_string(
                        'games/includes/ajax_pagination.html', pagination_context, request=request)

                    return JsonResponse({
                        'html': html,
                        'pagination_html': pagination_html,
                        'pagination_info': pagination_info,
                        'success': True,
                        'message': '数据加载成功'
                    })
                except Exception as e:
                    # 处理各种异常情况
                    logger.error(f"加载收藏游戏列表时出错: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': '加载数据失败，请刷新页面重试',
                        'details': str(e)
                    }, status=500)

            # 常规请求返回完整页面
            return render(request, 'games/user_profile.html', context)

        except Exception as e:
            logger.error(f"用户资料获取出错: {str(e)}")
            # 创建提示错误的上下文
            context = {
                'favorites': [],
                'history': [],
                'error_message': '获取用户资料出错，请稍后再试'
            }
            return render(request, 'games/user_profile.html', context)


class CategoryDetailView(DetailView):
    model = GameCategory
    template_name = 'games/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'category_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()

        # 获取子分类
        subcategories = GameCategory.objects.filter(
            parent=category, is_active=True)
        # 不需要手动设置game_count，因为它已经是一个计算属性
        context['subcategories'] = subcategories

        # 获取本分类及其所有子分类的游戏
        category_ids = [category.id]
        category_ids.extend(subcategories.values_list('id', flat=True))

        # 搜索查询
        search_query = self.request.GET.get('search', '')
        if search_query:
            game_queryset = Game.objects.filter(
                Q(categories__id__in=category_ids) &
                Q(status='online') &
                (Q(title__icontains=search_query) |
                 Q(description__icontains=search_query))
            ).distinct()
        else:
            game_queryset = Game.objects.filter(
                categories__id__in=category_ids,
                status='online'
            ).distinct()

        # 排序选项
        sort_option = self.request.GET.get('sort', 'newest')
        if sort_option == 'newest':
            game_queryset = game_queryset.order_by('-created_at')
        elif sort_option == 'popular':
            game_queryset = game_queryset.order_by('-play_count')
        elif sort_option == 'rating':
            game_queryset = game_queryset.order_by('-rating')

        # 分页
        paginator = Paginator(game_queryset, 12)  # 每页12个游戏
        page = self.request.GET.get('page')
        try:
            games = paginator.page(page)
        except PageNotAnInteger:
            games = paginator.page(1)
        except EmptyPage:
            games = paginator.page(paginator.num_pages)

        context['games'] = games
        context['sort'] = sort_option
        context['search_query'] = search_query
        return context


class HotGamesView(ListView):
    """热门游戏页面视图"""
    model = Game
    template_name = 'games/hot_games.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_paginate_by(self, queryset):
        """自定义分页数量"""
        # 获取每页显示数量参数，默认为12
        per_page = self.request.GET.get('per_page')
        if per_page:
            try:
                # 限制每页显示数量在合理范围内
                per_page = int(per_page)
                if per_page in [12, 24, 36]:
                    return per_page
            except ValueError:
                pass
        return self.paginate_by  # 返回默认值

    def get_queryset(self):
        queryset = Game.objects.filter(status='online')

        # 处理搜索
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # 处理分类筛选（多选）
        category_filters = self.request.GET.getlist('category')
        if category_filters:
            queryset = queryset.filter(
                categories__slug__in=category_filters).distinct()

        # 处理评分筛选（多选）
        rating_filters = self.request.GET.getlist('rating')
        if rating_filters:
            try:
                # 创建Q对象用于or条件
                rating_q = Q()
                for rating in rating_filters:
                    rating_value = int(rating)
                    # 为每个评分范围创建条件
                    if rating_value == 5:
                        rating_q |= Q(rating__gte=5)
                    elif rating_value == 4:
                        rating_q |= Q(rating__gte=4, rating__lt=5)
                    elif rating_value == 3:
                        rating_q |= Q(rating__gte=3, rating__lt=4)
                    elif rating_value == 2:
                        rating_q |= Q(rating__gte=2, rating__lt=3)
                    elif rating_value == 1:
                        rating_q |= Q(rating__gte=1, rating__lt=2)
                # 应用评分筛选
                if rating_q:
                    queryset = queryset.filter(rating_q)
            except (ValueError, TypeError):
                pass

        # 处理排序
        sort_by = self.request.GET.get('sort', 'popular')
        if sort_by == 'popular':
            queryset = queryset.order_by('-play_count')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-rating')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = GameCategory.objects.filter(is_active=True)
        context['search_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'popular')
        context['per_page'] = self.request.GET.get(
            'per_page', self.paginate_by)

        # 获取当前选中的分类和评分
        context['current_categories'] = self.request.GET.getlist('category')
        context['current_ratings'] = self.request.GET.getlist('rating')

        # 为每个游戏添加"热门"标记，但保留创建时间供模板使用
        for game in context['games']:
            game.time_ago = '热门'

        return context

    def get(self, request, *args, **kwargs):
        """重写get方法，支持AJAX请求"""
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        # 判断是否为AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # 渲染游戏列表片段
            html = render_to_string(
                'games/includes/game_list_fragment.html',
                context,
                request=request)
            return JsonResponse({
                'html': html,
                'success': True
            })

        # 常规请求返回完整页面
        return self.render_to_response(context)


class NewGamesView(ListView):
    """最新上线游戏页面视图"""
    model = Game
    template_name = 'games/new_games.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_paginate_by(self, queryset):
        """自定义分页数量"""
        # 获取每页显示数量参数，默认为12
        per_page = self.request.GET.get('per_page')
        if per_page:
            try:
                # 限制每页显示数量在合理范围内
                per_page = int(per_page)
                if per_page in [12, 24, 36]:
                    return per_page
            except ValueError:
                pass
        return self.paginate_by  # 返回默认值

    def get_queryset(self):
        queryset = Game.objects.filter(status='online')

        # 时间筛选
        time_filter = self.request.GET.get('time')
        now = datetime.now()

        if time_filter == 'today':
            # 今天上线的游戏
            date_threshold = now.replace(
                hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(created_at__gte=date_threshold)
        elif time_filter == 'week':
            # 本周上线的游戏
            date_threshold = now - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=date_threshold)
        elif time_filter == 'month':
            # 本月上线的游戏
            date_threshold = now - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=date_threshold)
        else:
            # 默认展示所有新游戏，按创建时间排序
            pass

        # 游戏类型筛选
        game_types = self.request.GET.getlist('type')
        if game_types:
            queryset = queryset.filter(
                categories__slug__in=game_types).distinct()

        # 排序
        sort_by = self.request.GET.get('sort')
        if sort_by == 'rating':
            queryset = queryset.order_by('-rating')
        elif sort_by == 'plays':
            queryset = queryset.order_by('-play_count')
        else:  # 默认按上线时间排序
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 获取所有分类用于筛选
        context['categories'] = GameCategory.objects.filter(is_active=True)

        # 当前的筛选条件
        context['current_time_filter'] = self.request.GET.get('time', '')
        context['current_types'] = self.request.GET.getlist('type')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['per_page'] = self.request.GET.get(
            'per_page', self.paginate_by)

        # 为每个游戏添加上线时间描述
        now = datetime.now()

        for game in context['games']:
            delta = now - game.created_at.replace(tzinfo=None)

            if delta.days == 0:
                if delta.seconds < 3600:
                    game.time_ago = '刚刚上线'
                else:
                    game.time_ago = '今日上线'
            elif delta.days == 1:
                game.time_ago = '昨日上线'
            elif delta.days < 7:
                game.time_ago = f'{delta.days}天前'
            elif delta.days < 30:
                game.time_ago = '本周'
            else:
                game.time_ago = '本月'

        return context

    def get(self, request, *args, **kwargs):
        """重写get方法，支持AJAX请求"""
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        # 判断是否为AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # 渲染游戏列表片段
            html = render_to_string(
                'games/includes/game_list_fragment.html',
                context,
                request=request)
            return JsonResponse({
                'html': html,
                'success': True
            })

        # 常规请求返回完整页面
        return self.render_to_response(context)


class GameSearchView(ListView):
    """游戏搜索页面视图"""
    model = Game
    template_name = 'games/search.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_paginate_by(self, queryset):
        """自定义分页数量"""
        # 获取每页显示数量参数，默认为12
        per_page = self.request.GET.get('per_page')
        if per_page:
            try:
                # 限制每页显示数量在合理范围内
                per_page = int(per_page)
                if per_page in [12, 24, 36]:
                    return per_page
            except ValueError:
                pass
        return self.paginate_by  # 返回默认值

    def get_queryset(self):
        queryset = Game.objects.filter(status='online')

        # 搜索关键词
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()

        # 游戏类型筛选
        category_filters = self.request.GET.getlist('category')
        if category_filters:
            queryset = queryset.filter(
                categories__id__in=category_filters).distinct()

        # 评分筛选
        rating_filters = self.request.GET.getlist('rating')
        if rating_filters:
            rating_query = Q()
            for rating_filter in rating_filters:
                try:
                    rating_value = int(rating_filter)
                    rating_query |= Q(rating__gte=rating_value)
                except ValueError:
                    pass

            if rating_query:
                queryset = queryset.filter(rating_query)

        # 时间筛选 - 支持多选
        time_filters = self.request.GET.getlist('time')
        if time_filters:
            time_query = Q()
            now = datetime.now()

            for time_filter in time_filters:
                if time_filter == 'today':
                    # 今天上线的游戏
                    date_threshold = now.replace(
                        hour=0, minute=0, second=0, microsecond=0)
                    time_query |= Q(created_at__gte=date_threshold)
                elif time_filter == 'week':
                    # 本周上线的游戏
                    date_threshold = now - timedelta(days=7)
                    time_query |= Q(created_at__gte=date_threshold)
                elif time_filter == 'month':
                    # 本月上线的游戏
                    date_threshold = now - timedelta(days=30)
                    time_query |= Q(created_at__gte=date_threshold)

            # 应用时间筛选条件
            if time_query:
                queryset = queryset.filter(time_query)

        # 排序
        sort_by = self.request.GET.get('sort')
        if sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-rating')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-play_count')
        else:
            # 默认排序：相关性（对于搜索结果）
            if search_query:
                # 根据标题匹配度排序，完全匹配的排在前面
                queryset = sorted(
                    queryset,
                    key=lambda x: (
                        0 if x.title.lower() == search_query.lower() else
                        1 if search_query.lower() in x.title.lower() else
                        2
                    )
                )
            else:
                # 如果没有搜索词，默认按照热门程度排序
                queryset = queryset.order_by('-play_count')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 获取搜索关键词
        search_query = self.request.GET.get('q', '')
        context['search_query'] = search_query

        # 获取筛选条件
        context['selected_categories'] = self.request.GET.getlist('category')
        context['rating'] = self.request.GET.getlist('rating')
        context['time_filter'] = self.request.GET.getlist('time')
        context['current_sort'] = self.request.GET.get('sort')
        context['per_page'] = self.request.GET.get(
            'per_page', self.paginate_by)

        # 获取所有游戏的基础查询集(用于统计各分类游戏数量)
        base_queryset = Game.objects.filter(status='online')

        # 如果有搜索关键词，需要应用到基础查询集
        if search_query:
            base_queryset = base_queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()

        # 获取所有分类及其游戏数量 - 使用子查询以获取准确的计数
        categories = []
        for category in GameCategory.objects.filter(is_active=True):
            # 查询出该分类含有的游戏数量(基于当前搜索结果)
            count = base_queryset.filter(categories=category).count()
            category.games_count = count
            categories.append(category)

        context['categories'] = categories
        context['total_games'] = Game.objects.filter(status='online').count()

        # 添加评分统计信息
        rating_counts = {}
        for rating in range(1, 6):
            rating_counts[rating] = base_queryset.filter(
                rating__gte=rating).count()
        context['rating_counts'] = rating_counts

        return context

    def get(self, request, *args, **kwargs):
        """重写get方法，支持AJAX请求"""
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        # 判断是否为AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # 准备返回数据
            data = {
                'success': True,
                'search_query': context['search_query'],
                'total_games': len(context['games']),
                'per_page': context['per_page']
            }

            # 渲染游戏列表片段
            games_html = render_to_string(
                'games/includes/search_games_fragment.html',
                context,
                request=request)
            data['games_html'] = games_html

            # 渲染分页片段
            pagination_context = {
                'is_paginated': context['is_paginated'],
                'paginator': context['paginator'],
                'page_obj': context['page_obj'],
            }
            pagination_html = render_to_string(
                'games/includes/ajax_pagination.html',
                pagination_context,
                request=request)
            data['pagination_html'] = pagination_html

            return JsonResponse(data)

        # 常规请求返回完整页面
        return self.render_to_response(context)


class GameDetailByIdView(View):
    """通过ID访问游戏详情的视图"""

    def get(self, request, game_id):
        # 通过ID获取游戏
        try:
            game = Game.objects.get(id=game_id, status='online')
            logger.info(f"通过ID访问游戏: {game_id} - {game.title}")

            # 记录游戏播放
            if request.user.is_authenticated and hasattr(
                    request.user, 'is_member'):
                try:
                    # 尝试获取前台用户
                    front_user = FrontUser.objects.get(
                        username=request.user.username)

                    # 更新或创建游戏历史记录
                    try:
                        history, created = FrontGameHistory.objects.get_or_create(
                            user=front_user,
                            game=game,
                            defaults={'play_count': 1}
                        )

                        if not created:
                            # 如果记录已存在，增加播放次数
                            history.play_count += 1
                            history.save(
                                update_fields=[
                                    'play_count',
                                    'last_played'])

                        # 更新游戏总播放次数
                        game.play_count += 1
                        game.save(update_fields=['play_count'])

                        logger.info(
                            f"记录游戏播放 - 用户: {front_user.username}, 游戏: {game.title}")
                    except Exception as e:
                        logger.error(f"记录游戏播放出错 - 错误: {str(e)}")
                except FrontUser.DoesNotExist:
                    logger.warning(f"找不到对应的前台用户: {request.user.username}")

            # 重定向到游戏详情页
            return redirect('games:game_detail', game_slug=game.slug)

        except Game.DoesNotExist:
            logger.warning(f"尝试访问不存在的游戏ID: {game_id}")
            return render(request, '404.html', status=404)


@method_decorator(login_required, name='dispatch')
class ProfileSettingsView(View):
    """用户设置页面视图"""

    def get(self, request):
        user = request.user
        try:
            # 获取是否显示会员内容的配置
            show_member_content = ConfigSettings.get_config('show_member_content', True)
            if isinstance(show_member_content, str):
                show_member_content = show_member_content.lower() not in ('false', '0')
            
            # 获取或创建用户资料
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # 获取用户的收藏游戏
            favorites = FrontGameFavorite.objects.filter(user=user).select_related('game')
            
            # 获取用户的游戏历史
            history = FrontGameHistory.objects.filter(user=user).select_related('game')
            
            # 获取社交账号信息
            from allauth.socialaccount.models import SocialAccount
            google_account = SocialAccount.objects.filter(user=user, provider='google').first()
            
            context = {
                'user': user,
                'profile': profile,
                'favorites': favorites,
                'history': history,
                'active_tab': 'settings',
                'show_member_content': show_member_content,  # 添加会员内容显示配置
                'google_account': google_account,  # 添加Google社交账号信息
                'has_google_account': google_account is not None,  # 添加是否有Google账号的标记
            }
            return render(request, 'games/profile_settings.html', context)
        except Exception as e:
            logger.error(f"访问设置页面时出错: {str(e)}")
            messages.error(request, _('访问设置页面时发生错误，请稍后再试'))
            return redirect('games:profile_settings')


@method_decorator(login_required, name='dispatch')
class UpdateProfileView(View):
    """更新用户个人资料 - 支持API调用"""

    def post(self, request):
        user = request.user

        try:
            # 获取或创建用户资料
            from .models import UserProfile
            from core.api_utils import api_response
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            profile, created = UserProfile.objects.get_or_create(user=user)

            # 更新邮箱
            email = request.POST.get('email')
            verification_code = request.POST.get('verification_code')

            if email and email != user.email:
                # 验证验证码
                cache_key = f'email_verification_{user.id}'
                verification_data = cache.get(cache_key)
                
                if not verification_data:
                    return api_response(
                        success=False,
                        message=_('验证码已过期，请重新获取'),
                        code='validation_error'
                    )
                
                if verification_data['email'] != email:
                    return api_response(
                        success=False,
                        message=_('验证码与邮箱不匹配'),
                        code='validation_error'
                    )
                
                if verification_data['code'] != verification_code:
                    return api_response(
                        success=False,
                        message=_('验证码错误'),
                        code='validation_error'
                    )
                
                # 检查邮箱是否已存在
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    return api_response(
                        success=False,
                        message=_('该邮箱已被使用'),
                        code='duplicate_entry'
                    )
                
                # 验证通过，更新邮箱
                user.email = email
                # 清除验证码缓存
                cache.delete(cache_key)

            # 处理随机头像URL
            if 'random_avatar_url' in request.POST and request.POST.get('random_avatar_url'):
                # 保存随机头像URL
                random_avatar_url = request.POST.get('random_avatar_url')
                profile.avatar_url = random_avatar_url
                # 清除已上传的头像
                if profile.avatar:
                    profile.avatar = None

            # 保存用户信息
            user.save()
            profile.save()

            # 构建响应数据
            profile_data = {
                'username': user.username,
                'email': user.email,
                'avatar_url': profile.avatar_url,
                'has_avatar': bool(profile.avatar),
                'avatar_path': profile.avatar.url if profile.avatar else None,
            }

            # 返回JSON响应，不进行重定向
            return api_response(
                success=True,
                message=_('个人资料已更新'),
                data=profile_data,
                code='success'
            )

        except Exception as e:
            logger.error(f"更新用户资料时出错: {str(e)}")
            
            # 返回错误JSON响应
            return api_response(
                success=False,
                message=_('更新个人资料时发生错误，请稍后再试'),
                code='internal_error',
                errors={'details': str(e)}
            )


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    """更改密码视图"""
    
    def post(self, request):
        try:
            # 获取表单数据
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # 验证当前密码
            if not request.user.check_password(current_password):
                return JsonResponse({
                    'success': False,
                    'message': '当前密码错误'
                })
            
            # 验证新密码和确认密码一致
            if new_password != confirm_password:
                return JsonResponse({
                    'success': False,
                    'message': '两次输入的密码不一致'
                })
            
            # 验证新密码强度
            try:
                validate_password(new_password, request.user)
            except ValidationError as errors:
                return JsonResponse({
                    'success': False,
                    'message': '密码强度不足: ' + ', '.join([str(e) for e in errors])
                })
            
            # 更新密码
            request.user.set_password(new_password)
            request.user.save()
            
            # 确保用户保持登录状态
            update_session_auth_hash(request, request.user)
            
            return JsonResponse({
                'success': True,
                'message': '密码更新成功'
            })
        except Exception as e:
            logger.error(f"更改密码时出错: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '更改密码时发生错误，请稍后再试'
            })


@method_decorator(login_required, name='dispatch')
class DeleteAccountView(LoginRequiredMixin, View):
    """删除账号视图"""
    
    def post(self, request):
        try:
            # 验证密码
            password = request.POST.get('password')
            if not request.user.check_password(password):
                return JsonResponse({
                    'success': False,
                    'message': '密码错误'
                })
            
            # 删除用户
            user = request.user
            user.delete()
            
            # 清除会话
            logout(request)
            
            return JsonResponse({
                'success': True,
                'message': '账号已成功删除'
            })
            
        except Exception as e:
            logger.error(f"删除账号时出错: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '删除账号失败，请稍后重试'
            })


@method_decorator(login_required, name='dispatch')
class ProfileHistoryView(ListView):
    """用户游戏历史记录视图"""
    model = FrontGameHistory
    template_name = 'games/profile_history.html'
    context_object_name = 'game_history'
    paginate_by = 12

    def get_queryset(self):
        """获取当前用户的游戏历史记录"""
        return FrontGameHistory.objects.filter(
            user=self.request.user
        ).select_related('game').order_by('-last_played')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 获取是否显示会员内容的配置
        show_member_content = ConfigSettings.get_config('show_member_content', True)
        if isinstance(show_member_content, str):
            show_member_content = show_member_content.lower() not in ('false', '0')
        context['show_member_content'] = show_member_content

        # 添加页面标题
        context['title'] = '游戏历史'

        # 添加用户信息
        context['user'] = self.request.user

        # 获取或创建用户资料
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user)
        context['profile'] = profile

        # 查询用户的收藏游戏，用于profile_header模板
        favorites = FrontGameFavorite.objects.filter(user=self.request.user)
        context['favorites'] = favorites

        # 查询用户的游戏历史，用于profile_header模板
        history = FrontGameHistory.objects.filter(user=self.request.user)
        context['history'] = history

        # 添加统计信息
        total_games = self.get_queryset().count()
        total_play_time = sum(
            history.play_count for history in self.get_queryset())

        context['total_games'] = total_games
        context['total_play_time'] = total_play_time

        return context


@method_decorator(login_required, name='dispatch')
class ProfileMembershipView(TemplateView):
    """用户会员信息视图"""
    template_name = 'games/profile_membership.html'

    def get(self, request, *args, **kwargs):
        # 检查是否启用会员内容显示
        show_member_content = ConfigSettings.get_config('show_member_content', True)
        if isinstance(show_member_content, str):
            show_member_content = show_member_content.lower() not in ('false', '0')
            
        if not show_member_content:
            # 如果配置为不显示会员内容，则重定向到首页
            messages.info(request, '会员功能暂时不可用')
            return redirect('games:home')
            
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 获取用户个人资料
        profile, created = UserProfile.objects.get_or_create(user=user)
        context['profile'] = profile
        
        # 检查会员状态
        context['is_member'] = profile.is_member
        context['member_until'] = profile.member_until
        context['membership_type'] = profile.member_type
        
        # 添加会员特权信息
        if profile.is_member:
            context['membership_features'] = MembershipFeature.objects.filter(
                membership_level__lte=self._get_membership_level(
                    profile.member_type), is_active=True)

        # 添加页面标题
        context['title'] = '会员信息'

        return context

    def _get_membership_level(self, member_type):
        """根据会员类型获取对应的等级"""
        levels = {
            'free': 0,
            'monthly': 1,
            'quarterly': 2,
            'yearly': 3
        }
        return levels.get(member_type, 0)

    def post(self, request, *args, **kwargs):
        """处理会员订阅请求"""
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': '请先登录后再进行订阅'
            }, status=403)

        membership_type = request.POST.get('membership_type')
        billing_cycle = request.POST.get('billing_cycle')

        # 更新用户会员状态
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.member_type = int(membership_type)
            profile.save()

            return JsonResponse({
                'status': 'success',
                'message': '订阅成功',
                'redirect_url': reverse('games:profile')
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'处理出错: {str(e)}'
            }, status=500)


@method_decorator(login_required, name='dispatch')
class FavoritesApiView(View):
    """获取用户收藏的游戏API视图"""

    def get(self, request):
        try:
            # 获取用户资料
            profile, created = UserProfile.objects.get_or_create(user=request.user)

            # 查询用户收藏数据，使用select_related优化查询
            favorites_query = FrontGameFavorite.objects.filter(
                user=request.user
            ).select_related(
                'game'
            ).prefetch_related(
                'game__categories'
            )

            # 处理搜索查询
            search_query = request.GET.get('search', '')
            if search_query:
                favorites_query = favorites_query.filter(
                    Q(game__title__icontains=search_query) |
                    Q(game__description__icontains=search_query)
                ).distinct()

            # 处理分类筛选
            category_id = request.GET.get('category', '')
            if category_id and category_id.isdigit():
                favorites_query = favorites_query.filter(
                    game__categories__id=int(category_id)
                ).distinct()

            # 设置排序
            sort_by = request.GET.get('sort', 'recent')
            if sort_by == 'recent':
                favorites_query = favorites_query.order_by('-created_at')  # 按收藏时间倒序
            elif sort_by == 'name':
                favorites_query = favorites_query.order_by('game__title')  # 按游戏名称升序
            elif sort_by == 'rating':
                favorites_query = favorites_query.order_by('-game__rating')  # 按评分降序

            # 分页处理
            page = request.GET.get('page', 1)
            per_page = request.GET.get('per_page', 12)

            try:
                page = int(page)
                per_page = int(per_page)
                if per_page not in [12, 24, 36, 48]:  # 限制每页显示数量选项
                    per_page = 12
            except (ValueError, TypeError):
                page = 1
                per_page = 12

            # 使用正确的per_page值创建分页器
            paginator = Paginator(favorites_query, per_page)

            try:
                favorites_page = paginator.page(page)
            except PageNotAnInteger:
                favorites_page = paginator.page(1)
            except EmptyPage:
                # 如果请求的页面超出范围，返回最后一页
                favorites_page = paginator.page(paginator.num_pages)

            # 构建游戏数据列表
            favorites_data = []
            for favorite in favorites_page:
                game = favorite.game
                
                # 获取游戏分类
                categories = [
                    {
                        'id': category.id,
                        'name': category.name,
                        'slug': category.slug
                    }
                    for category in game.categories.all()
                ]

                # 构建游戏数据
                game_data = {
                    'id': game.id,
                    'title': game.title,
                    'slug': game.slug,
                    'thumbnail': game.thumbnail.url if game.thumbnail else '',
                    'description': game.description,
                    'short_description': game.summary,
                    'rating': float(game.rating) if game.rating else 0,
                    'play_count': game.play_count,
                    'is_featured': game.is_featured,
                    'is_premium': game.is_premium if hasattr(game, 'is_premium') else False,
                    'price': float(game.price) if hasattr(game, 'price') and game.price else 0,
                    'categories': categories,
                    'favorite_id': favorite.id,
                    'created_at': favorite.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                favorites_data.append(game_data)

            # 构建分页信息
            pagination_info = {
                'current_page': favorites_page.number,
                'num_pages': paginator.num_pages,
                'has_next': favorites_page.has_next(),
                'has_previous': favorites_page.has_previous(),
                'next_page_number': favorites_page.next_page_number() if favorites_page.has_next() else None,
                'previous_page_number': favorites_page.previous_page_number() if favorites_page.has_previous() else None,
                'start_index': favorites_page.start_index(),
                'end_index': favorites_page.end_index(),
                'per_page': per_page,
                'total_items': paginator.count,
            }

            # 返回JSON格式的数据
            return JsonResponse({
                'favorites': favorites_data,
                'pagination': pagination_info,
                'filters': {
                    'search': search_query,
                    'category': category_id,
                    'sort': sort_by
                },
                'success': True,
                'message': '数据加载成功'
            })
        except Exception as e:
            # 处理各种异常情况
            logger.error(f"API加载收藏游戏列表时出错: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': '加载数据失败，请稍后再试',
                'details': str(e)
            }, status=500)


def register(request):
    """用户注册视图 - 使用Django默认User模型"""
    from django.urls import reverse
    from django.shortcuts import redirect, render
    from django.contrib import messages
    from django.utils.translation import gettext as _
    from django.contrib.auth import login as auth_login
    from .forms import UserRegistrationForm

    # 检查注册功能是否开启
    enable_register = ConfigSettings.get_config('enable_register', True)
    if isinstance(enable_register, str):
        enable_register = enable_register.lower() not in ('false', '0')
    
    if not enable_register:
        # 如果注册功能关闭，添加提示并重定向到首页
        messages.warning(request, _('注册功能当前已关闭'))
        return redirect('games:home')

    if request.user.is_authenticated:
        # 用户已登录，重定向到首页
        return redirect('games:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # 保存用户并创建用户资料
            user = form.save()

            # 登录用户
            auth_login(request, user)

            # 添加成功消息
            messages.success(request, _('注册成功！欢迎加入GameHub！'))

            # 重定向到首页或个人资料页
            next_url = request.GET.get('next', reverse('games:home'))
            return redirect(next_url)
    else:
        form = UserRegistrationForm()

    # 添加 allauth_enabled 标志
    context = {
        'form': form,
        'title': _('注册新账号'),
        'allauth_enabled': True,  # 添加这一行，让模板知道使用 allauth 表单
    }
    return render(request, 'games/registration/register.html', context)


@login_required
def profile(request):
    """用户个人资料视图，重定向到用户个人中心"""
    # 这个函数不再需要创建UserProfileView实例
    # 因为/profile/路径现在直接映射到UserProfileView
    return redirect('games:profile')


def logout_view(request):
    """登出视图"""
    # 使用Django的logout函数注销用户
    logout(request)

    # 重定向到首页
    return redirect('/')


class FrontendLoginView(LoginView):
    """
    前台用户登录视图
    使用Django默认认证后端
    """
    template_name = 'games/registration/login.html'
    form_class = LoginForm  # 使用自定义登录表单
    redirect_authenticated_user = True  # 启用对已认证用户的重定向
    
    def dispatch(self, request, *args, **kwargs):
        """检查是否允许登录"""
        # 从配置中获取是否开放登录
        enable_login = ConfigSettings.get_config('enable_login', True)
        
        # 如果配置值是字符串的'false'或'0'，则认为是False
        if isinstance(enable_login, str):
            enable_login = enable_login.lower() not in ('false', '0')
            
        if not enable_login:
            # 如果不允许登录，重定向到首页并添加消息
            messages.warning(request, _('登录功能当前已关闭'))
            return redirect('games:home')
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加 allauth_enabled 标记和 login_form 变量，使模板能正确识别 django-allauth 的表单
        context['allauth_enabled'] = True
        context['login_form'] = context.get('form')
        
        # 获取tab参数，用于确定显示登录还是注册选项卡
        context['tab'] = self.request.GET.get('tab', 'login')
        
        return context
    
    def get_success_url(self):
        """获取登录成功后的重定向URL"""
        redirect_to = self.request.GET.get('next') or self.request.POST.get('next')
        if redirect_to and url_has_allowed_host_and_scheme(redirect_to, allowed_hosts={self.request.get_host()}):
            return redirect_to
        return reverse('games:home')  # 默认重定向到首页
    
    def form_valid(self, form):
        """使用Django默认的登录流程"""
        # 使用Django默认的login处理
        auth_login(self.request, form.get_user())

        # 记录登录信息
        logger = logging.getLogger('games')
        logger.info(f"用户登录成功: 用户={form.get_user().username}")

        # 确保用户有资料，如果没有则创建
        user = form.get_user()
        UserProfile.objects.get_or_create(user=user)

        # 重定向到成功URL
        return redirect(self.get_success_url())


def debug_session(request):
    """
    用于调试会话的视图函数
    仅在开发环境中使用
    """
    from django.http import JsonResponse
    import logging
    import datetime
    import json
    from django.db import connection

    logger = logging.getLogger('games')

    # 获取关于会话的信息
    session_data = {
        'session_key': request.session.session_key,
        'session_cookie_name': getattr(
            request.session,
            'cookie_name',
            'sessionid'),
        'session_cookie_path': getattr(
            request.session,
            'cookie_path',
            '/'),
        'is_authenticated': request.user.is_authenticated,
        'session_data': dict(
            request.session),
        'session_engine': request.session.__class__.__name__,
        'cookie_data': {
            k: v for k,
            v in request.COOKIES.items()}}

    # 记录会话状态
    if request.user.is_authenticated:
        user_info = {
            'username': request.user.username,
            'user_id': request.user.id,
            'is_staff': getattr(request.user, 'is_staff', False)
        }
        session_data['user_info'] = user_info
        logger.info(f"已登录用户的会话状态: {session_data}")
    else:
        logger.info(f"未登录用户的会话状态: {session_data}")

    # 检查前台会话表中是否有记录
    session_records = []
    if request.session.session_key:
        try:
            frontend_sessions = FrontendSession.objects.filter(
                session_key=request.session.session_key)
            for session in frontend_sessions:
                session_records.append({
                    'session_key': session.session_key,
                    'user_id': session.user_id,
                    'expire_date': session.expire_date.isoformat() if session.expire_date else None
                })

                # 解码会话数据
                try:
                    if hasattr(request.session, 'decode'):
                        decoded_data = request.session.decode(
                            session.session_data)
                        session_records[-1]['decoded_data'] = decoded_data
                except Exception as e:
                    session_records[-1]['decode_error'] = str(e)
        except Exception as e:
            logger.error(f"查询前台会话记录时出错: {str(e)}")
            session_records = [{'error': str(e)}]

    session_data['frontend_session_records'] = session_records

    # 查询所有的当前用户会话记录
    if request.user.is_authenticated:
        try:
            user_id = request.user.id
            user_sessions = FrontendSession.objects.filter(user_id=user_id)
            user_session_records = []

            for session in user_sessions:
                user_session_records.append({
                    'session_key': session.session_key,
                    'expire_date': session.expire_date.isoformat() if session.expire_date else None,
                    'is_current': session.session_key == request.session.session_key
                })

            session_data['user_sessions'] = user_session_records
        except Exception as e:
            logger.error(f"查询用户会话记录时出错: {str(e)}")
            session_data['user_sessions_error'] = str(e)

    # 尝试保存会话以确保其工作正常
    if not request.session.session_key:
        request.session.save()
        logger.info(f"创建了新的会话，session_key={request.session.session_key}")
        session_data['new_session_key'] = request.session.session_key

    # 将当前时间作为会话值存储，用于验证
    request.session['debug_timestamp'] = datetime.datetime.now().isoformat()
    request.session['user_id'] = request.user.id if request.user.is_authenticated else None
    request.session.save()

    # 检查会话保存后是否出现在数据库中
    if request.session.session_key:
        try:
            with connection.cursor() as cursor:
                # 查询前台会话表
                cursor.execute(
                    "SELECT COUNT(*) FROM frontend_sessions WHERE session_key = %s", [
                        request.session.session_key])
                frontend_count = cursor.fetchone()[0]

                # 查询Django默认会话表
                cursor.execute(
                    "SELECT COUNT(*) FROM django_session WHERE session_key = %s", [
                        request.session.session_key])
                django_count = cursor.fetchone()[0]

                session_data['db_status'] = {
                    'frontend_sessions_count': frontend_count,
                    'django_session_count': django_count
                }
        except Exception as e:
            logger.error(f"查询数据库会话状态时出错: {str(e)}")
            session_data['db_status_error'] = str(e)

    return JsonResponse(session_data)


class MembershipPlansView(TemplateView):
    """会员计划页面视图"""
    template_name = 'games/membership_plans.html'

    def get(self, request, *args, **kwargs):
        # 检查是否启用会员内容显示
        show_member_content = ConfigSettings.get_config('show_member_content', True)
        if isinstance(show_member_content, str):
            show_member_content = show_member_content.lower() not in ('false', '0')
            
        if not show_member_content:
            # 如果配置为不显示会员内容，则重定向到首页
            messages.info(request, '会员功能暂时不可用')
            return redirect('games:home')
            
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 获取当前用户会员信息
        current_membership = 0
        if self.request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=self.request.user)
                current_membership = profile.member_type
            except UserProfile.DoesNotExist:
                pass

        context['current_membership'] = current_membership
        return context

    def post(self, request, *args, **kwargs):
        """处理会员订阅请求"""
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': '请先登录后再进行订阅'
            }, status=403)

        membership_type = request.POST.get('membership_type')
        billing_cycle = request.POST.get('billing_cycle')

        # 更新用户会员状态
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.member_type = int(membership_type)
            profile.save()

            return JsonResponse({
                'status': 'success',
                'message': '订阅成功',
                'redirect_url': reverse('games:profile')
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'处理出错: {str(e)}'
            }, status=500)


@method_decorator(login_required, name='dispatch')
class GameHistoryApiView(View):
    """用户游戏历史API视图"""

    def get(self, request):
        try:
            # 获取查询参数
            search = request.GET.get('search', '')
            category_id = request.GET.get('category', '')
            sort_by = request.GET.get('sort', 'recent')
            page = request.GET.get('page', 1)
            per_page = request.GET.get('per_page', 12)
            get_categories = request.GET.get('get_categories', 'false').lower() == 'true'

            # 参数验证和转换
            try:
                page = int(page)
                per_page = int(per_page)
                if per_page not in [12, 24, 36, 48]:
                    per_page = 12
            except (ValueError, TypeError):
                page = 1
                per_page = 12

            # 转换排序参数
            sort_mapping = {
                'recent': '-last_played',
                'name': 'game__title',
                'rating': '-game__rating',
                'duration': '-play_count'
            }
            db_sort = sort_mapping.get(sort_by, '-last_played')

            # 获取用户的游戏历史
            history_query = FrontGameHistory.objects.filter(
                user=request.user
            ).select_related(
                'game'
            ).prefetch_related(
                'game__categories'
            )

            # 应用搜索过滤
            if search:
                history_query = history_query.filter(
                    Q(game__title__icontains=search) |
                    Q(game__description__icontains=search)
                ).distinct()

            # 应用分类过滤
            if category_id and category_id.isdigit():
                try:
                    category = GameCategory.objects.get(id=int(category_id))
                    history_query = history_query.filter(
                        game__categories=category
                    ).distinct()
                except GameCategory.DoesNotExist:
                    # 如果分类不存在，记录错误但不应用过滤
                    logger.warning(f"尝试过滤不存在的分类: {category_id}")
                except Exception as e:
                    # 处理其他可能的异常
                    logger.error(f"应用分类过滤时出错: {str(e)}")

            # 应用排序
            history_query = history_query.order_by(db_sort)

            # 获取分类列表(如果需要)
            categories_data = []
            if get_categories:
                # 获取有游戏历史记录的分类（使用正确的关联关系查询）
                # 获取当前用户有历史记录的游戏ID列表
                user_game_ids = FrontGameHistory.objects.filter(
                    user=request.user
                ).values_list('game_id', flat=True).distinct()
                
                # 获取这些游戏关联的分类
                categories = GameCategory.objects.filter(
                    games__id__in=user_game_ids
                ).distinct().order_by('name')
                
                categories_data = [
                    {
                        'id': category.id,
                        'name': category.name,
                        'slug': category.slug,
                        'count': FrontGameHistory.objects.filter(
                            user=request.user,
                            game__categories=category  # 直接使用category对象而不是id
                        ).count()
                    }
                    for category in categories
                ]

            # 分页
            paginator = Paginator(history_query, per_page)
            try:
                history_page = paginator.page(page)
            except PageNotAnInteger:
                history_page = paginator.page(1)
            except EmptyPage:
                history_page = paginator.page(paginator.num_pages)

            # 构建历史记录数据
            history_data = []
            for history in history_page:
                # 跳过无效记录
                if not history:
                    continue
                    
                # 确保game是Game对象
                try:
                    game = history.game
                    if not game:
                        # 提供一个替代记录
                        history_item = {
                            'id': history.id,
                            'play_count': history.play_count,
                            'duration': history.play_count * 15,  # 假设每次游玩15分钟
                            'last_played': history.last_played.strftime('%Y-%m-%d') if history.last_played else '',
                            'game': {
                                'id': 0,
                                'title': '游戏已删除',
                                'slug': '',
                                'thumbnail_url': '',
                                'rating': 0,
                                'summary': '',
                                'description': '',
                                'categories': [],
                                'category': ''
                            }
                        }
                        history_data.append(history_item)
                        continue
                        
                    if not isinstance(game, Game):
                        # 如果不是Game实例，记录错误并跳过
                        logger.error(f"游戏对象类型错误: game={game}, type={type(game)}")
                        continue
                except Exception as e:
                    logger.error(f"获取游戏对象时出错: history_id={history.id}, error={str(e)}")
                    continue
                
                # 获取游戏分类
                categories = []
                try:
                    categories = [
                        {
                            'id': category.id,
                            'name': category.name,
                            'slug': category.slug
                        }
                        for category in game.categories.all()
                    ]
                except Exception as e:
                    logger.error(f"获取游戏分类时出错: game_id={game.id if game else 'None'}, error={str(e)}")
                
                # 计算游戏时长（假设1次游玩=15分钟）
                duration = history.play_count * 15
                
                # 格式化时间
                last_played_formatted = None
                if history and history.last_played:
                    try:
                        # 格式化为相对时间（如"3天前"）
                        now = datetime.now(timezone.utc)
                        if hasattr(history.last_played, 'tzinfo') and history.last_played.tzinfo is None:
                            last_played = history.last_played.replace(tzinfo=timezone.utc)
                        else:
                            last_played = history.last_played
                            
                        delta = now - last_played
                        
                        if delta.days == 0:
                            if delta.seconds < 3600:
                                last_played_formatted = f"{delta.seconds // 60}分钟前"
                            else:
                                last_played_formatted = f"{delta.seconds // 3600}小时前"
                        elif delta.days == 1:
                            last_played_formatted = "昨天"
                        elif delta.days < 7:
                            last_played_formatted = f"{delta.days}天前"
                        elif delta.days < 30:
                            last_played_formatted = f"{delta.days // 7}周前"
                        else:
                            last_played_formatted = last_played.strftime('%Y-%m-%d')
                    except Exception as e:
                        logger.error(f"格式化时间出错: history_id={history.id}, error={str(e)}")
                        last_played_formatted = str(history.last_played)
                
                # 构建游戏数据 - 避免空引用
                if game:
                    # 获取主分类（如果存在）
                    primary_category = categories[0]['name'] if categories else ''
                    
                    history_item = {
                        'id': history.id,
                        'play_count': history.play_count,
                        'duration': duration,
                        'last_played': last_played_formatted or '',
                        'game': {
                            'id': game.id,
                            'title': game.title,
                            'slug': game.slug,
                            'thumbnail_url': game.thumbnail.url if game.thumbnail else '',
                            'rating': float(game.rating) if game.rating else 0,
                            'summary': game.summary or '',
                            'description': game.description or '',
                            'categories': categories,
                            'category': primary_category
                        }
                    }
                    history_data.append(history_item)
                else:
                    # 如果游戏不存在，提供基本信息
                    history_item = {
                        'id': history.id,
                        'play_count': history.play_count,
                        'duration': duration,
                        'last_played': last_played_formatted or '',
                        'game': {
                            'id': 0,
                            'title': '游戏已删除',
                            'slug': '',
                            'thumbnail_url': '',
                            'rating': 0,
                            'summary': '',
                            'description': '',
                            'categories': [],
                            'category': ''
                        }
                    }
                    history_data.append(history_item)

            # 构建响应数据
            response_data = {
                'success': True,
                'history': history_data,
                'pagination': {
                    'current_page': history_page.number,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': history_page.has_next(),
                    'has_previous': history_page.has_previous(),
                    'has_more': history_page.has_next()
                },
                'filters': {
                    'search': search,
                    'category': category_id,
                    'sort': sort_by
                }
            }
            
            # 只有在请求时才添加分类数据
            if get_categories:
                response_data['categories'] = categories_data

            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"游戏历史API错误: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '获取游戏历史数据失败，请稍后再试',
                'error': str(e)
            }, status=500)
            
    def post(self, request, history_id=None):
        """处理历史记录的删除和清空操作"""
        try:
            # 检查请求路径以确定操作类型
            path = request.path
            
            # 删除单个历史记录
            if history_id is not None and '/delete/' in path:
                try:
                    # 查找并验证所有权
                    history = get_object_or_404(FrontGameHistory, id=history_id, user=request.user)
                    game_title = history.game.title if history.game else '未知游戏'
                    
                    # 删除记录
                    history.delete()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f"已删除《{game_title}》的游戏记录",
                        'deleted_id': history_id
                    })
                except FrontGameHistory.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': "找不到该游戏记录"
                    }, status=404)
            
            # 清空所有历史记录
            elif '/clear/' in path:
                # 删除该用户的所有历史记录
                deleted_count, _ = FrontGameHistory.objects.filter(user=request.user).delete()
                
                return JsonResponse({
                    'success': True,
                    'message': f"已清空{deleted_count}条游戏历史记录",
                    'deleted_count': deleted_count
                })
            
            # 未知操作
            else:
                return JsonResponse({
                    'success': False,
                    'message': "未知操作"
                }, status=400)
                
        except Exception as e:
            logger.error(f"游戏历史API错误: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '操作失败，请稍后再试',
                'error': str(e)
            }, status=500)


@method_decorator(login_required, name='dispatch')
class SocialConnectView(View):
    """处理社交账号关联和解绑"""

    def post(self, request):
        try:
            action = request.POST.get('action')
            platform = request.POST.get('platform')

            if not action or not platform:
                return JsonResponse({
                    'success': False,
                    'message': '缺少必要参数'
                }, status=400)

            # 获取用户资料
            profile, created = UserProfile.objects.get_or_create(user=request.user)

            if action == 'link':
                # 这里应该实现实际的社交账号关联逻辑
                # 例如：调用社交平台的 OAuth 流程
                return JsonResponse({
                    'success': True,
                    'message': f'已成功关联{platform}账号'
                })
            elif action == 'unlink':
                # 这里应该实现实际的社交账号解绑逻辑
                # 例如：清除关联的社交账号信息
                return JsonResponse({
                    'success': True,
                    'message': f'已成功解绑{platform}账号'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '无效的操作类型'
                }, status=400)

        except Exception as e:
            logger.error(f"处理社交账号关联时出错: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '操作失败，请稍后再试'
            }, status=500)


class SendEmailVerificationView(View):
    """发送邮箱验证码"""
    
    def post(self, request):
        try:
            from django.contrib.auth.models import User
            email = request.POST.get('newEmail')
            
            # 验证邮箱格式
            if not email or '@' not in email:
                return api_response(
                    success=False,
                    message='请输入有效的邮箱地址',
                    code='validation_error'
                )
            
            # 检查邮箱是否已被使用
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                return api_response(
                    success=False,
                    message='该邮箱已被其他用户使用',
                    code='duplicate_entry'
                )
            
            # 生成6位数字验证码
            verification_code = ''.join(random.choices(string.digits, k=6))
            
            # 将验证码保存到缓存，设置5分钟过期
            cache_key = f'email_verification_{request.user.id}'
            cache.set(cache_key, {
                'code': verification_code,
                'email': email
            }, 300)  # 5分钟过期
            
            # 使用 core.mail 模块中的发送验证码函数
            from core.mail import send_verification_code
            send_result = send_verification_code(email, verification_code, fail_silently=False)
            
            if not send_result:
                logger.error(f"发送邮箱验证码失败，邮箱: {email}")
                return api_response(
                    success=False,
                    message='发送验证码失败，请检查邮箱配置或稍后重试',
                    code='internal_error'
                )
            
            return api_response(
                success=True,
                message='验证码已发送',
                code='success'
            )
            
        except Exception as e:
            logger.error(f"发送邮箱验证码时出错: {str(e)}")
            return api_response(
                success=False,
                message='发送验证码失败，请稍后重试',
                code='internal_error'
            )


@method_decorator(login_required, name='dispatch')
class UpdateEmailView(View):
    """修改用户邮箱专用API"""
    
    def post(self, request):
        try:
            from django.contrib.auth.models import User
            
            # 获取请求数据
            email = request.POST.get('email')
            verification_code = request.POST.get('verification_code')
            
            # 验证必要参数
            if not email:
                return api_response(
                    success=False,
                    message='邮箱地址不能为空',
                    code='validation_error'
                )
                
            if not verification_code:
                return api_response(
                    success=False,
                    message='验证码不能为空',
                    code='validation_error'
                )
            
            # 验证邮箱格式
            if '@' not in email:
                return api_response(
                    success=False,
                    message='邮箱格式不正确',
                    code='validation_error'
                )
            
            # 检查是否与当前邮箱相同
            user = request.user
            if email == user.email:
                return api_response(
                    success=False,
                    message='新邮箱与当前邮箱相同',
                    code='validation_error'
                )
            
            # 检查邮箱是否已被其他用户使用
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return api_response(
                    success=False,
                    message='该邮箱已被其他用户使用',
                    code='duplicate_entry'
                )
            
            # 验证验证码
            cache_key = f'email_verification_{user.id}'
            verification_data = cache.get(cache_key)
            
            if not verification_data:
                return api_response(
                    success=False,
                    message='验证码已过期，请重新获取',
                    code='verification_expired'
                )
            
            if verification_data['email'] != email:
                return api_response(
                    success=False,
                    message='验证码与邮箱不匹配',
                    code='verification_mismatch'
                )
            
            if verification_data['code'] != verification_code:
                return api_response(
                    success=False,
                    message='验证码错误',
                    code='invalid_verification'
                )
            
            # 验证通过，更新邮箱
            old_email = user.email
            user.email = email
            user.save()
            
            # 清除验证码缓存
            cache.delete(cache_key)
            
            # 记录邮箱修改日志
            logger.info(f"用户 {user.username} 成功修改邮箱: {old_email} -> {email}")
            
            return api_response(
                success=True,
                message='邮箱修改成功',
                code='success',
                data={
                    'email': email
                }
            )
            
        except Exception as e:
            logger.error(f"修改邮箱时出错: {str(e)}")
            return api_response(
                success=False,
                message='修改邮箱失败，请稍后重试',
                code='internal_error'
            )


class RegisterVerificationCodeView(View):
    """发送注册邮箱验证码"""
    
    def post(self, request):
        try:
            from django.contrib.auth.models import User
            email = request.POST.get('email')
            
            # 验证邮箱格式
            if not email or '@' not in email:
                return api_response(
                    success=False,
                    message='请输入有效的邮箱地址',
                    code='validation_error'
                )
            
            # 检查邮箱是否已被使用
            if User.objects.filter(email=email).exists():
                return api_response(
                    success=False,
                    message='该邮箱已被注册',
                    code='duplicate_entry'
                )
            
            # 生成6位数字验证码
            verification_code = ''.join(random.choices(string.digits, k=6))
            
            # 将验证码保存到缓存，设置10分钟过期
            # 使用邮箱作为缓存key，因为用户还未登录没有ID
            cache_key = f'register_verification_{email}'
            cache.set(cache_key, {
                'code': verification_code,
                'email': email,
                'created_at': datetime.now().timestamp()
            }, 600)  # 10分钟过期
            
            # 使用 core.mail 模块中的发送验证码函数
            from core.mail import send_verification_code
            send_result = send_verification_code(email, verification_code, fail_silently=False)
            
            if not send_result:
                logger.error(f"发送注册验证码失败，邮箱: {email}")
                return api_response(
                    success=False,
                    message='发送验证码失败，请检查邮箱配置或稍后重试',
                    code='internal_error'
                )
            
            return api_response(
                success=True,
                message='验证码已发送，有效期10分钟',
                code='success'
            )
            
        except Exception as e:
            logger.error(f"发送注册验证码时出错: {str(e)}")
            return api_response(
                success=False,
                message='发送验证码失败，请稍后重试',
                code='internal_error'
            )


class RegisterApiView(View):
    """用户注册API视图 - 支持异步注册和邮箱验证"""
    
    def post(self, request):
        try:
            from django.contrib.auth.models import User
            from django.contrib.auth import login as auth_login
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError
            
            # 获取表单数据 - 适配 allauth 表单和原生表单
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            verification_code = request.POST.get('verification_code', '').strip()
            # 处理不同表单的同意条款字段
            agree_terms = request.POST.get('agree_terms') == 'on' or request.POST.get('terms') == 'on'
            
            # 验证表单数据
            errors = {}
            
            # 验证用户名
            if not username:
                errors['username'] = ['用户名不能为空']
            elif len(username) < 3:
                errors['username'] = ['用户名太短，至少需要3个字符']
            elif len(username) > 30:
                errors['username'] = ['用户名太长，最多30个字符']
            elif not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
                errors['username'] = ['用户名只能包含字母、数字、下划线或中文']
            elif User.objects.filter(username=username).exists():
                errors['username'] = ['该用户名已被使用']
                
            # 验证邮箱
            if not email:
                errors['email'] = ['邮箱不能为空']
            elif '@' not in email:
                errors['email'] = ['请输入有效的邮箱地址']
            elif User.objects.filter(email=email).exists():
                errors['email'] = ['该邮箱已被注册']
                
            # 验证密码
            if not password1:
                errors['password1'] = ['密码不能为空']
            else:
                try:
                    # 使用Django内置的密码验证
                    validate_password(password1)
                except ValidationError as e:
                    errors['password1'] = list(e.messages)
                    
            if not password2:
                errors['password2'] = ['请确认密码']
            elif password1 != password2:
                errors['password2'] = ['两次输入的密码不一致']
                
            # 验证服务条款
            if not agree_terms:
                # 根据表单类型返回不同的字段错误
                if 'terms' in request.POST:
                    errors['terms'] = ['请阅读并同意用户协议和隐私政策']
                else:
                    errors['agree_terms'] = ['请阅读并同意用户协议和隐私政策']
                
            # 验证验证码
            if not verification_code:
                errors['verification_code'] = ['请输入验证码']
            else:
                # 从缓存获取验证码
                cache_key = f'register_verification_{email}'
                cached_data = cache.get(cache_key)
                
                if not cached_data:
                    errors['verification_code'] = ['验证码已过期，请重新获取']
                elif cached_data['code'] != verification_code:
                    errors['verification_code'] = ['验证码错误']
                elif cached_data['email'] != email:
                    errors['verification_code'] = ['验证码与邮箱不匹配']
            
            # 如果有错误，返回错误信息
            if errors:
                # 将所有错误信息合并成一条消息
                error_messages = []
                for field, field_errors in errors.items():
                    for error in field_errors:
                        # 格式化错误消息，包含字段名
                        field_display = {
                            'username': '用户名',
                            'email': '邮箱',
                            'password1': '密码',
                            'password2': '确认密码',
                            'verification_code': '验证码',
                            'terms': '服务条款',
                            'agree_terms': '服务条款'
                        }.get(field, field)
                        error_messages.append(f"{field_display}：{error}")
                
                # 将错误消息以换行符连接
                error_message = "、".join(error_messages)
                
                return api_response(
                    success=False,
                    message=error_message,
                    errors=errors,  # 仍然保留原始errors对象以兼容现有代码
                    code='validation_error'
                )
                
            # 创建用户
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            
            # 创建用户资料 - 使用get_or_create避免重复创建
            UserProfile.objects.get_or_create(user=user)
            
            # 清除验证码缓存
            cache.delete(f'register_verification_{email}')
            
            # 登录用户 - 明确指定使用Django的默认认证后端
            from django.contrib.auth.backends import ModelBackend
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # 返回成功响应
            return api_response(
                success=True,
                message='注册成功！欢迎加入GameHub！',
                data={
                    'redirect': request.GET.get('next', reverse('games:home'))
                },
                code='success'
            )
            
        except Exception as e:
            logger.error(f"注册过程中出错: {str(e)}")
            return api_response(
                success=False,
                message='注册失败，请稍后重试',
                code='internal_error'
            )


class ForgotPasswordView(View):
    """基于邮箱验证码的找回密码视图"""
    template_name = 'games/registration/forgot_password.html'
    
    def get(self, request):
        """展示找回密码页面"""
        return render(request, self.template_name)
