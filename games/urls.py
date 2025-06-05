from django.urls import path
from . import views
from .views_category import CategoryDetailView
from .views_ad import ad_click

app_name = 'games'

urlpatterns = [
    # 首页
    path('', views.HomeView.as_view(), name='home'),
    
    # 游戏列表
    path('games/', views.GameListView.as_view(), name='game_list'),
    path('category/<slug:category_slug>/games/', views.GameListView.as_view(), name='game_list_by_category'),
    
    # 游戏详情
    path('game/<slug:game_slug>/', views.GameDetailView.as_view(), name='game_detail'),
    
    # 分类相关
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:category_slug>/', CategoryDetailView.as_view(), name='category_detail'),
    
    # 用户相关功能已移除
    
    # 广告相关
    path('ad-click/<int:ad_id>/', ad_click, name='ad_click'),
]