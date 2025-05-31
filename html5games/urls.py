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
    path('admin/', admin.site.urls),
    # 游戏应用URL
    path('', include('games.urls')),
    # 添加语言后缀
    prefix_default_language=True
)

# 开发环境下的媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
