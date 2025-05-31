from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    Game, Category, Advertisement
)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'categories', 'is_featured', 'is_active', 'created_at')
    list_filter = ('is_featured', 'is_active', 'categories')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    
    def categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    categories.short_description = _('分类')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'order', 'display_icon')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent', 'order', 'is_active')
        }),
        (_('Visuals'), {
            'fields': ('image', 'icon_class'),
            'description': _('You can either use an image or a Font Awesome icon. If both are provided, the icon will be used as a fallback if the image fails to load.')
        }),
    )

    def display_icon(self, obj):
        if obj.icon_class:
            return format_html('<i class="{0}"></i> {0}', obj.icon_class)
        return '-'
    display_icon.short_description = _('Icon')


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'is_active', 'start_date', 'end_date')
    list_filter = ('position', 'is_active')
    search_fields = ('name', 'content')
    date_hierarchy = 'start_date'





