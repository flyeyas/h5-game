from django.db import models
from django.utils.translation import gettext_lazy as _
from cms.models.pluginmodel import CMSPlugin
from .models import Category

class GameListPlugin(CMSPlugin):
    LIST_TYPE_CHOICES = (
        ('featured', _('Featured Games')),
        ('popular', _('Popular Games')),
        ('newest', _('Newest Games')),
        ('category', _('Category Games')),
    )
    
    title = models.CharField(_('Title'), max_length=200, blank=True)
    list_type = models.CharField(_('List Type'), max_length=20, choices=LIST_TYPE_CHOICES, default='featured')
    category = models.ForeignKey(Category, verbose_name=_('Category'), null=True, blank=True, 
                                on_delete=models.SET_NULL, related_name='game_list_plugins')
    max_items = models.PositiveIntegerField(_('Maximum Items'), default=8)
    show_more_link = models.BooleanField(_('Show More Link'), default=True)
    more_link_text = models.CharField(_('More Link Text'), max_length=50, default=_('View All'))
    more_link_url = models.CharField(_('More Link URL'), max_length=200, blank=True)

    class Meta:
        verbose_name = _('Game List Plugin')
        verbose_name_plural = _('Game List Plugins')

class CategoryListPlugin(CMSPlugin):
    title = models.CharField(_('Title'), max_length=200, blank=True)
    show_parent_only = models.BooleanField(_('Show Parent Categories Only'), default=True)
    parent_category = models.ForeignKey(Category, verbose_name=_('Parent Category'), null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name='category_list_plugins')
    max_items = models.PositiveIntegerField(_('Maximum Items'), default=8)
    show_more_link = models.BooleanField(_('Show More Link'), default=True)
    more_link_text = models.CharField(_('More Link Text'), max_length=50, default=_('View All'))
    more_link_url = models.CharField(_('More Link URL'), max_length=200, blank=True)

    class Meta:
        verbose_name = _('Category List Plugin')
        verbose_name_plural = _('Category List Plugins') 