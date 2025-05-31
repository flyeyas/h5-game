from django.urls import path
from . import views
from .views_category import CategoryDetailView
from .views_ad import ad_click
from .views_admin import (
    AdminDashboardView, AdminGameListView, AdminGameCreateView, AdminGameUpdateView, AdminGameDeleteView,
    AdminCategoryListView, AdminCategoryCreateView, AdminCategoryUpdateView, AdminCategoryDeleteView,
    AdminAdListView, AdminAdCreateView,
    AdminAdUpdateView, AdminAdDeleteView, AdminStatsView, AdminSettingsView
)

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
    
    # 管理后台相关
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # 游戏管理
    path('admin/games/', AdminGameListView.as_view(), name='admin_game_list'),
    path('admin/games/create/', AdminGameCreateView.as_view(), name='admin_game_create'),
    path('admin/games/<int:pk>/edit/', AdminGameUpdateView.as_view(), name='admin_game_edit'),
    path('admin/games/<int:pk>/delete/', AdminGameDeleteView.as_view(), name='admin_game_delete'),
    
    # 分类管理
    path('admin/categories/', AdminCategoryListView.as_view(), name='admin_category_list'),
    path('admin/categories/create/', AdminCategoryCreateView.as_view(), name='admin_category_create'),
    path('admin/categories/<int:pk>/edit/', AdminCategoryUpdateView.as_view(), name='admin_category_edit'),
    path('admin/categories/<int:pk>/delete/', AdminCategoryDeleteView.as_view(), name='admin_category_delete'),
    
    # 用户管理功能已移除
    
    # 广告管理
    path('admin/ads/', AdminAdListView.as_view(), name='admin_ad_list'),
    path('admin/ads/create/', AdminAdCreateView.as_view(), name='admin_ad_create'),
    path('admin/ads/<int:pk>/edit/', AdminAdUpdateView.as_view(), name='admin_ad_edit'),
    path('admin/ads/<int:pk>/delete/', AdminAdDeleteView.as_view(), name='admin_ad_delete'),
    
    # 设置
    path('admin/settings/', AdminSettingsView.as_view(), name='admin_settings'),
]