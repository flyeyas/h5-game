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
from games.views_admin import (
    game_edit_json, toggle_game_status, add_user_modal,
    toggle_user_staff, toggle_user_superuser, toggle_user_active,
    get_permissions_api, add_group_modal, get_group_data, edit_group_modal
)

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

# Internationalization URLs
urlpatterns += i18n_patterns(
    # Custom logout view that supports GET method
    path('admin/logout/', games_views.custom_logout, name='custom_logout'),
    # Game edit API - use api prefix to avoid being captured by admin
    path('api/games/<int:game_id>/edit-json/', game_edit_json, name='game_edit_json'),
    # Game status toggle API
    path('api/games/<int:game_id>/toggle-status/', toggle_game_status, name='toggle_game_status'),
    # User add modal API
    path('api/users/add-modal/', add_user_modal, name='add_user_modal'),
    # User status toggle API
    path('api/users/<int:user_id>/toggle-staff/', toggle_user_staff, name='toggle_user_staff'),
    path('api/users/<int:user_id>/toggle-superuser/', toggle_user_superuser, name='toggle_user_superuser'),
    path('api/users/<int:user_id>/toggle-active/', toggle_user_active, name='toggle_user_active'),
    # User group management API
    path('api/permissions/', get_permissions_api, name='get_permissions_api'),
    path('api/groups/add-modal/', add_group_modal, name='add_group_modal'),
    path('api/groups/<int:group_id>/json/', get_group_data, name='get_group_data'),
    path('api/groups/<int:group_id>/edit/', edit_group_modal, name='edit_group_modal'),
    # Use custom admin site (based on Django admin secondary development)
    path('admin/', admin_site.urls),
    # Keep Django default admin as backup
    path('django-admin/', admin.site.urls),
    # Game application URLs
    path('', include('games.urls')),
    # Add language suffix
    prefix_default_language=True
)

# Media file service in development environment
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
