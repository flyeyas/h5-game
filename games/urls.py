from django.urls import path
from . import views
from .views_category import CategoryDetailView
from .views_ad import ad_click
from . import views_admin

app_name = 'games'

urlpatterns = [
    # 游戏前台视图
    path('', views.HomeView.as_view(), name='home'),
    path('games/', views.GameListView.as_view(), name='game_list'),
    path('games/category/<slug:category_slug>/', views.GameListView.as_view(), name='game_list_by_category'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('game/<slug:game_slug>/', views.GameDetailView.as_view(), name='game_detail'),
    path('category/<slug:category_slug>/', CategoryDetailView.as_view(), name='category_detail'),
    
    # 广告相关
    path('ad-click/<int:ad_id>/', ad_click, name='ad_click'),
    
    # 管理员API
    path('api/game/<int:game_id>/json/', views_admin.game_edit_json, name='game_edit_json'),
    path('api/game/<int:game_id>/toggle-status/', views_admin.toggle_game_status, name='toggle_game_status'),
    path('api/category/add/', views_admin.add_category_modal, name='add_category_modal'),
    path('api/category/<int:category_id>/json/', views_admin.get_category_data, name='get_category_data'),
    path('api/category/<int:category_id>/edit/', views_admin.edit_category_modal, name='edit_category_modal'),
    path('api/category/<int:category_id>/view/', views_admin.view_category_modal, name='view_category_modal'),
    path('api/category/<int:category_id>/delete/', views_admin.delete_category_modal, name='delete_category_modal'),
]