from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
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
    list_display = ('id', 'name', 'slug', 'parent', 'is_active', 'display_icon')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    # 移除prepopulated_fields，因为我们现在使用自动生成
    # prepopulated_fields = {'slug': ('name',)}
    change_list_template = 'admin/games/category/change_list.html'
    list_per_page = 5  # 每页显示5条记录，便于测试分页功能
    ordering = ['id']  # 按ID升序排列
    readonly_fields = ('slug',)  # 将slug设为只读
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent', 'is_active')
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

    def changelist_view(self, request, extra_context=None):
        """
        自定义分类列表视图，处理分页参数转换
        """
        # 处理分页参数转换：将 page 参数转换为 Django admin 标准的 p 参数
        if 'page' in request.GET and 'p' not in request.GET:
            # 创建一个新的 QueryDict 来修改参数
            get_params = request.GET.copy()
            get_params['p'] = get_params.pop('page')[0]
            request.GET = get_params

        return super().changelist_view(request, extra_context)

    def get_urls(self):
        """添加自定义URL"""
        from django.urls import path
        from .views_admin import toggle_category_status
        urls = super().get_urls()
        custom_urls = [
            path('<int:category_id>/toggle-status/', self.admin_site.admin_view(toggle_category_status), name='toggle_category_status'),
        ]
        return custom_urls + urls


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'ad_type', 'ad_size', 'is_active', 'click_count', 'view_count', 'revenue')
    list_filter = ('position', 'ad_type', 'is_active', 'ad_size')
    search_fields = ('name', 'adsense_unit_id', 'adsense_publisher_id')
    date_hierarchy = 'start_date'
    change_list_template = 'admin/games/advertisement/change_list.html'
    change_form_template = 'admin/games/advertisement/change_form.html'
    list_per_page = 5  # 每页显示5条记录，便于测试分页功能

    def get_queryset(self, request):
        """确保使用正确的查询集"""
        return super().get_queryset(request)

    fieldsets = (
        (None, {
            'fields': ('name', 'position', 'ad_type', 'ad_size', 'is_active')
        }),
        (_('Content'), {
            'fields': ('image', 'url', 'html_code'),
            'description': _('Upload an image or provide HTML code for the advertisement.')
        }),
        (_('Google AdSense'), {
            'fields': ('adsense_publisher_id', 'adsense_unit_id', 'adsense_slot_id'),
            'description': _('Google AdSense configuration for this advertisement.'),
            'classes': ('collapse',),
        }),
        (_('Schedule'), {
            'fields': ('start_date', 'end_date'),
            'description': _('Set the time period during which the advertisement will be displayed.')
        }),
        (_('Statistics'), {
            'fields': ('click_count', 'view_count', 'revenue', 'ctr'),
            'classes': ('collapse',),
            'description': _('Performance metrics for this advertisement.')
        }),
    )
    
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
        # 检查 Google AdSense 连接状态
        adsense_status = self.check_adsense_connection()

        # 准备额外的上下文数据
        if extra_context is None:
            extra_context = {}

        extra_context.update({
            'adsense_connected': adsense_status['connected'],
            'adsense_publisher_id': adsense_status['publisher_id'],
            'adsense_message': adsense_status['message'],
            'valid_ads_count': adsense_status['valid_ads_count'],
        })

        # 调用父类方法获取标准的changelist视图
        return super().changelist_view(request, extra_context)

    def check_adsense_connection(self):
        """
        检查 Google AdSense 连接状态
        """
        # 获取所有广告单元
        all_ads = Advertisement.objects.all()

        # 查找有效的 AdSense Publisher ID
        valid_publisher_ids = []
        valid_ads_count = 0

        for ad in all_ads:
            if (ad.adsense_publisher_id and
                ad.adsense_publisher_id != 'ca-pub-XXXXXXXXXXXXXXXX' and
                ad.adsense_publisher_id.strip() != '' and
                'ca-pub-' in ad.adsense_publisher_id and
                not 'XXXX' in ad.adsense_publisher_id and  # 排除包含 XXXX 的占位符
                len(ad.adsense_publisher_id) > 15):  # 确保是完整的 Publisher ID

                if ad.adsense_publisher_id not in valid_publisher_ids:
                    valid_publisher_ids.append(ad.adsense_publisher_id)
                valid_ads_count += 1

        # 判断连接状态
        if valid_publisher_ids:
            return {
                'connected': True,
                'publisher_id': valid_publisher_ids[0],  # 使用第一个有效的 Publisher ID
                'message': _('Your Google AdSense account is successfully connected. You can manage ad units, view revenue data, and optimize ad display performance.'),
                'valid_ads_count': valid_ads_count,
            }
        else:
            return {
                'connected': False,
                'publisher_id': None,
                'message': _('Google AdSense is not configured. Please add your AdSense Publisher ID to your ad units to enable revenue tracking and reporting.'),
                'valid_ads_count': 0,
            }

    def get_urls(self):
        """添加自定义URL"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('update-adsense-settings/', self.admin_site.admin_view(self.update_adsense_settings), name='update_adsense_settings'),
            path('verify-adsense-connection/', self.admin_site.admin_view(self.verify_adsense_connection), name='verify_adsense_connection'),
        ]
        return custom_urls + urls

    def update_adsense_settings(self, request):
        """更新 AdSense 设置"""
        if request.method == 'POST':
            try:
                global_publisher_id = request.POST.get('global_publisher_id', '').strip()
                update_existing = request.POST.get('update_existing') == 'on'

                # 验证 Publisher ID 格式
                if global_publisher_id and not self.validate_publisher_id(global_publisher_id):
                    return JsonResponse({
                        'success': False,
                        'message': _('Invalid Publisher ID format. It should start with "ca-pub-" followed by 16 digits.')
                    })

                updated_count = 0

                if update_existing and global_publisher_id:
                    # 更新所有现有的广告单元
                    ads_to_update = Advertisement.objects.all()
                    for ad in ads_to_update:
                        ad.adsense_publisher_id = global_publisher_id
                        ad.save()
                        updated_count += 1

                return JsonResponse({
                    'success': True,
                    'message': _('AdSense settings updated successfully. {} ad units updated.').format(updated_count)
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': _('An error occurred while updating settings: {}').format(str(e))
                })

        return JsonResponse({'success': False, 'message': _('Invalid request method.')})

    def verify_adsense_connection(self, request):
        """验证 AdSense 连接"""
        if request.method == 'POST':
            try:
                import json
                from .adsense_api import adsense_service

                data = json.loads(request.body)
                publisher_id = data.get('publisher_id', '').strip()

                # 使用真实的AdSense API进行验证
                success, verification_result = adsense_service.verify_publisher_id(publisher_id)

                return JsonResponse(verification_result)

            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'status': 'error',
                    'message': _('Invalid JSON data.')
                })
            except Exception as e:
                # 记录详细错误信息
                import logging
                logger = logging.getLogger('games')
                logger.error(f'AdSense verification error: {e}', exc_info=True)

                return JsonResponse({
                    'success': False,
                    'status': 'error',
                    'message': _('An error occurred during verification: {}').format(str(e))
                })

        return JsonResponse({
            'success': False,
            'status': 'error',
            'message': _('Invalid request method.')
        })



    def validate_publisher_id(self, publisher_id):
        """验证 Publisher ID 格式"""
        from .adsense_api import adsense_service
        return adsense_service.validate_publisher_id_format(publisher_id)


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


# 自定义UserAdmin，设置每页显示10条记录
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active')  # 在username前添加id列
    list_per_page = 10  # 设置每页显示10条记录
    ordering = ['id']  # 按ID正序排列
    change_list_template = 'admin/auth/user/change_list.html'

    def has_delete_permission(self, request, obj=None):
        """
        控制删除权限，禁止删除ID为1的用户
        """
        # 如果是ID为1的用户，禁止删除
        if obj and obj.id == 1:
            return False
        # 其他情况使用默认权限检查
        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        """
        为ID为1的用户设置只读字段，防止修改关键状态
        """
        readonly_fields = list(super().get_readonly_fields(request, obj))

        # 如果是ID为1的用户，将关键字段设为只读
        if obj and obj.id == 1:
            readonly_fields.extend(['is_staff', 'is_superuser', 'is_active'])

        return readonly_fields

# 自定义GroupAdmin，设置每页显示10条记录
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
class CustomGroupAdmin(BaseGroupAdmin):
    list_per_page = 10  # 设置每页显示10条记录
    ordering = ['id']  # 按ID正序排列
    change_list_template = 'admin/auth/group/change_list.html'


# 创建自定义admin站点实例
admin_site = CustomAdminSite(name='custom_admin')

# 重新注册所有模型到自定义admin站点
admin_site.register(Game, GameAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Advertisement, AdvertisementAdmin)

# 注册Django内置模型
from django.contrib.auth.models import User, Group
admin_site.register(User, CustomUserAdmin)  # 使用自定义的UserAdmin
admin_site.register(Group, CustomGroupAdmin)  # 使用自定义的GroupAdmin





