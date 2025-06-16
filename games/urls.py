from django.urls import path
from . import views
from .views_category import CategoryDetailView
from .views_ad import ad_click, ad_view, ad_statistics, revenue_reports, toggle_ad_status, edit_ad_ajax
from . import views_admin

app_name = 'games'

urlpatterns = [
    # Game frontend views
    path('', views.HomeView.as_view(), name='home'),
    path('games/', views.GameListView.as_view(), name='game_list'),
    path('games/category/<slug:category_slug>/', views.GameListView.as_view(), name='game_list_by_category'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('game/<slug:game_slug>/', views.GameDetailView.as_view(), name='game_detail'),
    path('category/<slug:category_slug>/', CategoryDetailView.as_view(), name='category_detail'),

    # Advertisement related
    path('ad-click/<int:ad_id>/', ad_click, name='ad_click'),
    path('ad-view/<int:ad_id>/', ad_view, name='ad_view'),
    path('api/ad-statistics/', ad_statistics, name='ad_statistics'),
    path('api/revenue-reports/', revenue_reports, name='revenue_reports'),
    path('api/ads/<int:ad_id>/toggle-status/', toggle_ad_status, name='toggle_ad_status'),
    path('api/ads/<int:ad_id>/edit/', edit_ad_ajax, name='edit_ad_ajax'),

    # Admin API
    path('api/game/<int:game_id>/json/', views_admin.game_edit_json, name='game_edit_json'),
    path('api/game/<int:game_id>/toggle-status/', views_admin.toggle_game_status, name='toggle_game_status'),
    path('api/category/add/', views_admin.add_category_modal, name='add_category_modal'),
    path('api/category/<int:category_id>/json/', views_admin.get_category_data, name='get_category_data'),
    path('api/category/<int:category_id>/edit/', views_admin.edit_category_modal, name='edit_category_modal'),
    path('api/category/<int:category_id>/view/', views_admin.view_category_modal, name='view_category_modal'),
    path('api/category/<int:category_id>/delete/', views_admin.delete_category_modal, name='delete_category_modal'),
]