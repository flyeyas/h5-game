from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from .models import Game, Category, UserProfile, GameHistory
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import translate_url
from django.conf import settings
from django.views.i18n import set_language


class HomeView(TemplateView):
    """首页视图"""
    template_name = 'games/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_games'] = Game.objects.filter(is_featured=True, is_active=True)[:6]
        context['latest_games'] = Game.objects.filter(is_active=True).order_by('-created_at')[:8]
        context['popular_games'] = Game.objects.filter(is_active=True).order_by('-view_count')[:8]
        context['categories'] = Category.objects.filter(parent=None)[:6]
        
        # 设置占位符标志
        context['placeholder_hero_image'] = False
        context['placeholder_featured_games'] = False
        context['placeholder_popular_games'] = False
        context['placeholder_new_games'] = False
        context['placeholder_categories'] = False
        context['placeholder_why_choose_us'] = False
        
        return context


class GameListView(ListView):
    """游戏列表视图"""
    model = Game
    template_name = 'games/game_list.html'
    context_object_name = 'games'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Game.objects.filter(is_active=True)
        
        # 分类过滤
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(categories=category)
        
        # 搜索过滤
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
            
        # 排序
        sort = self.request.GET.get('sort', 'latest')
        if sort == 'popular':
            queryset = queryset.order_by('-view_count')
        elif sort == 'rating':
            queryset = queryset.order_by('-rating')
        else:  # latest
            queryset = queryset.order_by('-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 分类信息
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
        
        # 搜索信息
        context['search_query'] = self.request.GET.get('q', '')
        context['sort'] = self.request.GET.get('sort', 'latest')
        
        # 侧边栏数据
        context['categories'] = Category.objects.all()
        context['popular_games'] = Game.objects.filter(is_active=True).order_by('-view_count')[:5]
        
        return context


class GameDetailView(DetailView):
    """游戏详情视图"""
    model = Game
    template_name = 'games/game_detail.html'
    context_object_name = 'game'
    slug_url_kwarg = 'game_slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.get_object()
        
        # 相关游戏
        categories = game.categories.all()
        related_games = Game.objects.filter(
            categories__in=categories, 
            is_active=True
        ).exclude(id=game.id).distinct()[:4]
        context['related_games'] = related_games
        
        # 评论
        context['comments'] = game.comments.filter(is_approved=True).order_by('-created_at')
        
        # 用户收藏状态
        if self.request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=self.request.user)
                context['is_favorite'] = game in user_profile.favorite_games.all()
            except UserProfile.DoesNotExist:
                context['is_favorite'] = False
        
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        game = self.get_object()
        
        # 增加浏览次数
        game.view_count += 1
        game.save(update_fields=['view_count'])
        
        # 记录游戏历史
        if request.user.is_authenticated:
            GameHistory.objects.create(user=request.user, game=game)
        
        return response


@login_required
def toggle_favorite(request, game_id):
    """切换游戏收藏状态"""
    game = get_object_or_404(Game, id=game_id)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if game in profile.favorite_games.all():
        profile.favorite_games.remove(game)
        is_favorite = False
    else:
        profile.favorite_games.add(game)
        is_favorite = True
    
    return JsonResponse({'status': 'success', 'is_favorite': is_favorite})


class CategoryListView(ListView):
    """分类列表视图"""
    model = Category
    template_name = 'games/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(parent=None)


@method_decorator(login_required, name='dispatch')
class UserProfileView(TemplateView):
    """用户资料视图"""
    template_name = 'games/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
        
        context['profile'] = profile
        context['favorite_games'] = profile.favorite_games.all()
        context['game_history'] = GameHistory.objects.filter(user=user).order_by('-played_at')[:10]
        
        return context


def custom_set_language(request):
    """
    自定义的语言切换视图，优化URL处理
    基于Django内置set_language视图，但改进了URL转换
    """
    # 调用Django原始的set_language视图来处理语言切换的基本逻辑
    response = set_language(request)
    
    # 如果是重定向响应且用户指定了next参数
    if isinstance(response, HttpResponseRedirect) and request.method == 'POST':
        next_url = request.POST.get('next', request.GET.get('next'))
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            # 获取被激活的语言
            language = translation.get_language()
            # 翻译URL（处理i18n_patterns中的URL）
            try:
                # 尝试生成翻译后的URL
                translated_url = translate_url(next_url, language)
                if translated_url != next_url:
                    # 如果URL发生了变化，使用新的URL重定向
                    return HttpResponseRedirect(translated_url)
            except:
                # 如果翻译过程中出错，保持原来的响应
                pass
    
    return response