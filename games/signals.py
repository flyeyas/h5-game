# 简化的信号处理器，移除CMS相关功能
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Game, Category

@receiver(post_save, sender=Game)
def game_saved(sender, instance, **kwargs):
    """当游戏被保存时清除相关缓存"""
    cache.delete('featured_games')
    cache.delete('popular_games')
    cache.delete('new_games')

@receiver(post_save, sender=Category)
def category_saved(sender, instance, **kwargs):
    """当分类被保存时清除相关缓存"""
    cache.delete('categories_menu')