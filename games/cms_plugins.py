from django.utils.translation import gettext_lazy as _
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from .models import Game, Category
from .models_cms import GameListPlugin, CategoryListPlugin

@plugin_pool.register_plugin
class GameListPlugin(CMSPluginBase):
    model = GameListPlugin
    name = _('Game List')
    render_template = 'games/cms_plugins/game_list.html'
    cache = True

    def render(self, context, instance, placeholder):
        games = Game.objects.filter(is_active=True)
        
        if instance.list_type == 'featured':
            games = games.filter(is_featured=True)
        elif instance.list_type == 'popular':
            games = games.order_by('-view_count')
        elif instance.list_type == 'newest':
            games = games.order_by('-created_at')
        elif instance.list_type == 'category' and instance.category:
            games = games.filter(categories=instance.category)
        
        games = games[:instance.max_items]
        context.update({
            'games': games,
            'title': instance.title,
            'show_more_link': instance.show_more_link,
            'more_link_text': instance.more_link_text,
            'more_link_url': instance.more_link_url,
        })
        return context

@plugin_pool.register_plugin
class CategoryListPlugin(CMSPluginBase):
    model = CategoryListPlugin
    name = _('Category List')
    render_template = 'games/cms_plugins/category_list.html'
    cache = True

    def render(self, context, instance, placeholder):
        categories = Category.objects.filter(is_active=True)
        
        if instance.show_parent_only:
            categories = categories.filter(parent__isnull=True)
        elif instance.parent_category:
            categories = categories.filter(parent=instance.parent_category)
        
        categories = categories.order_by('order', 'name')[:instance.max_items]
        context.update({
            'categories': categories,
            'title': instance.title,
            'show_more_link': instance.show_more_link,
            'more_link_text': instance.more_link_text,
            'more_link_url': instance.more_link_url,
        })
        return context 