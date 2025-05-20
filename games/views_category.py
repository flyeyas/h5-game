from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import Category, Game


class CategoryDetailView(DetailView):
    """分类详情视图"""
    model = Category
    template_name = 'games/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'category_slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        # 获取该分类下的热门游戏
        popular_games = Game.objects.filter(
            categories=category,
            is_active=True
        ).order_by('-view_count')[:8]
        context['popular_games'] = popular_games
        
        # 获取所有游戏（用于显示游戏数量）
        games = Game.objects.filter(categories=category, is_active=True)
        context['games'] = games
        
        # 获取相关分类（同级分类）
        if category.parent:
            # 如果是子分类，获取同一父分类下的其他子分类
            related_categories = Category.objects.filter(
                parent=category.parent
            ).exclude(id=category.id)[:4]
        else:
            # 如果是主分类，获取其他主分类
            related_categories = Category.objects.filter(
                parent=None
            ).exclude(id=category.id)[:4]
        
        context['related_categories'] = related_categories
        
        return context