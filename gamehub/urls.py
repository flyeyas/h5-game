from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    # 添加自定义管理面板URLs
    path('admin/', include('admin_panel.urls', namespace='admin_panel')),
    
    # 前台页面路径 - 放在 allauth URLs 之前，优先匹配我们的自定义登录视图
    path('', include('games.urls')),
    
    # django-allauth URLs - 放在后面，避免覆盖我们的自定义登录视图
    path('accounts/', include('allauth.urls')),
    
    # 通用登录路径重定向
    # path('login/', RedirectView.as_view(url='/accounts/login/'), name='login_root'),
]

# 在开发环境中添加媒体文件URL
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)