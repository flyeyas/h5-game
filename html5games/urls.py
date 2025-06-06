"""URL configuration for html5games project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from games.sitemaps import GameSitemap, CategorySitemap, StaticSitemap
from games import views as games_views
from games.admin import admin_site
from games.views_admin import game_edit_json, toggle_game_status, add_user_modal

# 站点地图配置
sitemaps = {
    'games': GameSitemap,
    'categories': CategorySitemap,
    'static': StaticSitemap,
}

# 非国际化URL
urlpatterns = [
    # 国际化切换
    path('i18n/setlang/', games_views.custom_set_language, name='set_language'),
    # 站点地图
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# 国际化URL
urlpatterns += i18n_patterns(
    # 自定义登出视图，支持GET方法
    path('admin/logout/', games_views.custom_logout, name='custom_logout'),
    # 游戏编辑API - 使用api前缀避免被admin捕获
    path('api/games/<int:game_id>/edit-json/', game_edit_json, name='game_edit_json'),
    # 游戏状态切换API
    path('api/games/<int:game_id>/toggle-status/', toggle_game_status, name='toggle_game_status'),
    # 用户添加模态框API
    path('api/users/add-modal/', add_user_modal, name='add_user_modal'),
    # 使用自定义admin站点 (基于Django admin二次开发)
    path('admin/', admin_site.urls),
    # 保留Django默认admin作为备用
    path('django-admin/', admin.site.urls),
    # 游戏应用URL
    path('', include('games.urls')),
    # 添加语言后缀
    prefix_default_language=True
)

# 开发环境下的媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
