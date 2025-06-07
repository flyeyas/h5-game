from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
    change_list_template = 'admin/games/game/change_list.html'

    def categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    categories.short_description = _('分类')

    def changelist_view(self, request, extra_context=None):
        """
        自定义游戏列表视图，添加额外的上下文数据
        """
        extra_context = extra_context or {}

        # 添加分类列表用于筛选下拉菜单
        extra_context['categories'] = Category.objects.filter(is_active=True)

        # 获取游戏数据
        queryset = self.get_queryset(request)

        # 应用筛选
        if request.GET.get('category__id__exact'):
            category_id = request.GET.get('category__id__exact')
            queryset = queryset.filter(categories__id=category_id)

        if request.GET.get('is_active__exact') is not None:
            is_active = request.GET.get('is_active__exact') == '1'
            queryset = queryset.filter(is_active=is_active)

        if request.GET.get('is_featured__exact') is not None:
            is_featured = request.GET.get('is_featured__exact') == '1'
            queryset = queryset.filter(is_featured=is_featured)

        # 应用搜索
        search_term = request.GET.get('q')
        if search_term:
            queryset = queryset.filter(title__icontains=search_term)

        # 应用排序
        ordering = request.GET.get('o')
        if ordering == '1':
            queryset = queryset.order_by('-created_at')
        elif ordering == '2':
            queryset = queryset.order_by('-view_count')
        elif ordering == '3':
            queryset = queryset.order_by('-rating')
        elif ordering == '4':
            queryset = queryset.order_by('title')

        # 添加分页
        paginator = Paginator(queryset, 10)  # 每页显示10条
        page = request.GET.get('page')
        try:
            results = paginator.page(page)
        except PageNotAnInteger:
            # 如果page不是整数，返回第一页
            results = paginator.page(1)
        except EmptyPage:
            # 如果page超出范围，返回最后一页
            results = paginator.page(paginator.num_pages)

        extra_context['results'] = results
        extra_context['paginator'] = paginator
        extra_context['page_obj'] = results
        extra_context['cl'] = {'result_count': queryset.count()}

        return super().changelist_view(request, extra_context)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'order', 'display_icon')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    change_list_template = 'admin/games/category/change_list.html'
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
    change_list_template = 'admin/games/advertisement/change_list.html'
    
    def get_position_display(self, obj):
        position_map = {
            'header': _('Header'),
            'sidebar': _('Sidebar'),
            'game_between': _('Between Games'),
            'footer': _('Footer')
        }
        return position_map.get(obj.position, obj.position)
    get_position_display.short_description = _('Position')
    
    def get_is_active_display(self, obj):
        return _('Yes') if obj.is_active else _('No')
    get_is_active_display.short_description = _('Active')
    
    def changelist_view(self, request, extra_context=None):
        """
        自定义广告列表视图，添加额外的上下文数据
        """
        extra_context = extra_context or {}
        
        # 获取广告数据
        queryset = self.get_queryset(request)
        
        # 应用筛选
        if request.GET.get('position__exact'):
            position = request.GET.get('position__exact')
            queryset = queryset.filter(position=position)
            
        if request.GET.get('is_active__exact') is not None:
            is_active = request.GET.get('is_active__exact') == '1'
            queryset = queryset.filter(is_active=is_active)
            
        # 应用搜索
        search_term = request.GET.get('q')
        if search_term:
            queryset = queryset.filter(name__icontains=search_term)
            
        # 应用排序
        ordering = request.GET.get('o')
        if ordering == '1':
            queryset = queryset.order_by('name')
        elif ordering == '2':
            queryset = queryset.order_by('position')
        elif ordering == '3':
            queryset = queryset.order_by('-is_active')
        elif ordering == '4':
            queryset = queryset.order_by('start_date')
        elif ordering == '5':
            queryset = queryset.order_by('end_date')
            
        # 添加分页
        paginator = Paginator(queryset, 10)  # 每页显示10条
        page = request.GET.get('page')
        try:
            results = paginator.page(page)
        except PageNotAnInteger:
            # 如果page不是整数，返回第一页
            results = paginator.page(1)
        except EmptyPage:
            # 如果page超出范围，返回最后一页
            results = paginator.page(paginator.num_pages)
            
        extra_context['results'] = results
        extra_context['paginator'] = paginator
        extra_context['page_obj'] = results
        extra_context['cl'] = {'result_count': queryset.count(), 'result_list': results.object_list}
        
        return super().changelist_view(request, extra_context)


# 自定义AdminSite类，添加统计数据到首页
class CustomAdminSite(AdminSite):
    site_header = _('HTML5 Games Administration')
    site_title = _('HTML5 Games Admin')
    index_title = _('Welcome to HTML5 Games Administration')

    def index(self, request, extra_context=None):
        """
        自定义admin首页，添加统计数据
        """
        extra_context = extra_context or {}

        # 获取统计数据
        try:
            extra_context.update({
                'total_users': User.objects.count(),
                'total_games': Game.objects.count(),
                'total_categories': Category.objects.count(),
                'total_ads': Advertisement.objects.count(),
            })
        except Exception:
            # 如果数据库还没有创建表，使用默认值
            extra_context.update({
                'total_users': 0,
                'total_games': 0,
                'total_categories': 0,
                'total_ads': 0,
            })

        return super().index(request, extra_context)


# 自定义GroupAdmin，设置每页显示10条记录
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
class CustomGroupAdmin(BaseGroupAdmin):
    list_per_page = 10  # 设置每页显示10条记录
    change_list_template = 'admin/auth/group/change_list.html'


# 创建自定义admin站点实例
admin_site = CustomAdminSite(name='custom_admin')

# 重新注册所有模型到自定义admin站点
admin_site.register(Game, GameAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Advertisement, AdvertisementAdmin)

# 注册Django内置模型
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
admin_site.register(User, UserAdmin)
admin_site.register(Group, CustomGroupAdmin)  # 使用自定义的GroupAdmin





