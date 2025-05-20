from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Game, Category
from django.utils import timezone

class GameSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Game.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at or obj.created_at
    
    def location(self, obj):
        return reverse('games:game_detail', args=[obj.slug])

class CategorySitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.7
    
    def items(self):
        return Category.objects.all()
    
    def lastmod(self, obj):
        # 如果分类下有游戏，返回最新游戏的更新时间
        games = obj.games.filter(is_active=True).order_by('-updated_at')
        if games.exists():
            return games.first().updated_at
        return obj.updated_at
    
    def location(self, obj):
        return reverse('games:category_detail', args=[obj.slug])

class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    
    def items(self):
        return ['games:home', 'games:game_list', 'games:category_list']
    
    def lastmod(self, obj):
        return timezone.now()
    
    def location(self, obj):
        return reverse(obj)