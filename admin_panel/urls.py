from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views, admin_user_views, role_views, menu_views, permission_views, game_category_views, game_views, tag_views, site_settings_views, seo_settings_views, email_settings_views, sites_views, social_app_views, front_user_views
from .payment_views import PaymentGatewayListView, PaymentGatewayCreateView, PaymentGatewayUpdateView, PaymentGatewayDeleteView, PaymentGatewayConfigView, PaymentGatewayTestView, SubscriptionPlanListView, SubscriptionPlanCreateView, SubscriptionPlanUpdateView, SubscriptionPlanDeleteView, SubscriptionListView, SubscriptionDetailView, SubscriptionUpdateView
from .admin_auth_views import login_view, ajax_login_view
from django.contrib.auth.views import LogoutView
from .site_settings_views import site_settings_view, ajax_update_site_settings, clear_site_settings_cache
from .seo_settings_views import seo_settings_view, ajax_update_seo_settings
from .config_settings_views import config_settings_view, edit_config_setting, delete_config_setting, clear_config_cache
from .admin_site import admin_login_required, custom_staff_member_required

app_name = 'admin_panel'

urlpatterns = [
    # 登录相关URL
    path('login/', login_view, name='admin_login'),
    path('ajax-login/', ajax_login_view, name='admin_ajax_login'),
    path('logout/', LogoutView.as_view(next_page='/admin/login/'), name='logout'),
    path('admin-logout/', admin_login_required(views.admin_logout_view), name='admin_logout'),
    
    # 面板首页
    path('', admin_login_required(views.dashboard), name='dashboard'),
    
    # 管理员用户管理
    path('users/', admin_login_required(admin_user_views.list_admin_users), name='admin_users_list'),
    path('users/add/', admin_login_required(admin_user_views.create_admin_user), name='add_admin'),
    path('users/edit/<int:admin_id>/', admin_login_required(admin_user_views.update_admin_user), name='edit_admin'),
    path('users/delete/<int:admin_id>/', admin_login_required(admin_user_views.remove_admin_user), name='delete_admin'),
    path('users/toggle-status/<int:admin_id>/', admin_login_required(admin_user_views.switch_admin_status), name='toggle_admin_status'),
    path('users/get/<int:admin_id>/', admin_login_required(admin_user_views.get_admin_detail), name='get_admin_detail'),
    
    # 菜单管理
    path('menus/', admin_login_required(menu_views.menu_list), name='menu_list'),
    path('menus/add/', admin_login_required(menu_views.add_menu), name='add_menu'),
    path('menus/edit/<int:menu_id>/', admin_login_required(menu_views.edit_menu), name='edit_menu'),
    path('menus/delete/<int:menu_id>/', admin_login_required(menu_views.delete_menu), name='delete_menu'),
    path('menus/toggle-status/<int:menu_id>/', admin_login_required(menu_views.toggle_menu_status), name='toggle_menu_status'),
    path('menu/save-order/', admin_login_required(menu_views.save_menu_order), name='save_menu_order'),
    
    # 兼容单数形式的menu路由
    path('menu/<int:menu_id>/delete/', admin_login_required(menu_views.delete_menu), name='menu_delete_singular'),
    path('menu/<int:menu_id>/edit/', admin_login_required(menu_views.edit_menu), name='menu_edit_singular'),
    path('menu/add/', admin_login_required(menu_views.add_menu), name='menu_add_singular'),
    
    # 后台菜单管理
    path('backend-menus/', admin_login_required(menu_views.backend_menu_management), name='backend_menu_management'),
    path('menu/<int:menu_id>/get/', admin_login_required(menu_views.get_menu_detail), name='get_menu_detail'),

    # 用户管理
    path('admin-user/list/', admin_login_required(admin_user_views.list_admin_users), name='admin_list'),
    path('admin-user/add/', admin_login_required(admin_user_views.create_admin_user), name='add_admin_user'),
    path('admin-user/remove/', admin_login_required(admin_user_views.remove_admin_user), name='remove_admin_user'),
    path('admin-user/switch-status/', admin_login_required(admin_user_views.switch_admin_status), name='switch_admin_status'),
    path('admin-user/<int:user_id>/roles/', admin_login_required(role_views.user_roles_management), name='user_roles_management'),
    path('admin-user/<int:user_id>/save-roles/', admin_login_required(role_views.save_user_roles), name='save_user_roles'),

    # 前台用户管理
    path('front-users/', admin_login_required(front_user_views.list_front_users), name='front_users_list'),
    path('front-users/get/<int:user_id>/', admin_login_required(front_user_views.get_front_user_detail), name='get_front_user_detail'),
    path('front-users/toggle-status/<int:user_id>/', admin_login_required(front_user_views.toggle_front_user_status), name='toggle_front_user_status'),
    path('front-users/reset-password/<int:user_id>/', admin_login_required(front_user_views.reset_front_user_password), name='reset_front_user_password'),
    path('front-users/toggle-member/<int:user_id>/', admin_login_required(front_user_views.toggle_member_status), name='toggle_front_user_member'),
    path('front-users/extend-member/<int:user_id>/', admin_login_required(front_user_views.extend_member_until), name='extend_front_user_member'),

    # 角色管理
    path('roles/', admin_login_required(role_views.roles_list), name='roles_list'),
    path('roles/add/', admin_login_required(role_views.add_role), name='add_role'),
    path('roles/edit/<int:role_id>/', admin_login_required(role_views.edit_role), name='edit_role'),
    path('roles/delete/<int:role_id>/', admin_login_required(role_views.delete_role), name='delete_role'),
    path('roles/<int:role_id>/permissions/', admin_login_required(role_views.role_permissions), name='role_permissions'),
    path('roles/<int:role_id>/save-permissions/', admin_login_required(role_views.save_role_permissions), name='save_role_permissions'),

    # 游戏分类管理
    path('game-categories/', admin_login_required(game_category_views.game_category_list), name='game_category_list'),
    path('game-categories/create/', admin_login_required(game_category_views.game_category_create), name='game_category_create'),
    path('game-categories/update/<int:category_id>/', admin_login_required(game_category_views.game_category_update), name='game_category_update'),
    path('game-categories/delete/<int:category_id>/', admin_login_required(game_category_views.game_category_delete), name='game_category_delete'),
    path('game-categories/detail/<int:category_id>/', admin_login_required(game_category_views.game_category_detail), name='game_category_detail'),
    path('game-categories/toggle-status/<int:category_id>/', admin_login_required(game_category_views.game_category_toggle_status), name='game_category_toggle_status'),
    
    # 游戏管理
    path('games/', admin_login_required(game_views.game_list), name='game_list'),
    path('games/create/', admin_login_required(game_views.game_create), name='game_create'),
    path('games/update/<int:game_id>/', admin_login_required(game_views.game_update), name='game_update'),
    path('games/delete/<int:game_id>/', admin_login_required(game_views.game_delete), name='game_delete'),
    path('games/detail/<int:game_id>/', admin_login_required(game_views.game_detail), name='game_detail'),
    path('games/toggle-status/<int:game_id>/', admin_login_required(game_views.game_toggle_status), name='game_toggle_status'),
    
    # 游戏标签管理
    path('tags/', admin_login_required(tag_views.tag_list), name='tag_list'),
    path('tags/create/', admin_login_required(tag_views.tag_create), name='tag_create'),
    path('tags/detail/<int:tag_id>/', admin_login_required(tag_views.tag_detail), name='tag_detail'),
    path('tags/update/<int:tag_id>/', admin_login_required(tag_views.tag_update), name='tag_update'),
    path('tags/delete/<int:tag_id>/', admin_login_required(tag_views.tag_delete), name='tag_delete'),
    path('tags/toggle-status/<int:tag_id>/', admin_login_required(tag_views.tag_toggle_status), name='tag_toggle_status'),
    path('tags/all/', admin_login_required(tag_views.get_all_tags), name='get_all_tags'),
    
    # 网站设置
    path('site-settings/', admin_login_required(site_settings_views.site_settings_view), name='site_settings'),
    path('site-settings/clear-cache/', admin_login_required(site_settings_views.clear_site_settings_cache), name='clear_site_settings_cache'),
    path('site-settings/ajax-update/', admin_login_required(site_settings_views.ajax_update_site_settings), name='ajax_update_site_settings'),
    
    # Sites应用管理
    path('sites/', admin_login_required(sites_views.sites_list_view), name='sites_list'),
    path('sites/create/', admin_login_required(sites_views.site_create_view), name='site_create'),
    path('sites/edit/<int:site_id>/', admin_login_required(sites_views.site_edit_view), name='site_edit'),
    path('sites/delete/<int:site_id>/', admin_login_required(sites_views.site_delete_view), name='site_delete'),
    path('sites/ajax-update/<int:site_id>/', admin_login_required(sites_views.ajax_update_site), name='ajax_update_site'),
    
    # 社交应用管理
    path('social-apps/', admin_login_required(social_app_views.social_app_list_view), name='social_app_list'),
    path('social-apps/create/', admin_login_required(social_app_views.social_app_create_view), name='social_app_create'),
    path('social-apps/edit/<int:app_id>/', admin_login_required(social_app_views.social_app_edit_view), name='social_app_edit'),
    path('social-apps/delete/<int:app_id>/', admin_login_required(social_app_views.social_app_delete_view), name='social_app_delete'),
    path('social-apps/detail/<int:app_id>/', admin_login_required(social_app_views.social_app_detail_view), name='social_app_detail'),
    
    # 邮件设置
    path('email-settings/', admin_login_required(email_settings_views.email_settings_view), name='email_settings'),
    path('email-settings/clear-cache/', admin_login_required(email_settings_views.clear_email_settings_cache), name='clear_email_settings_cache'),
    path('email-settings/ajax-update/', admin_login_required(email_settings_views.ajax_update_email_settings), name='ajax_update_email_settings'),
    path('email-settings/test-email/', admin_login_required(email_settings_views.test_email), name='test_email'),
    
    # SEO设置
    path('seo-settings/', admin_login_required(seo_settings_views.seo_settings_view), name='seo_settings'),
    path('seo-settings/clear-cache/', admin_login_required(seo_settings_views.clear_seo_settings_cache), name='clear_seo_settings_cache'),
    path('seo-settings/ajax-update/', admin_login_required(seo_settings_views.ajax_update_seo_settings), name='ajax_update_seo_settings'),
    
    # 系统配置路由
    path('config-settings/', admin_login_required(config_settings_view), name='config_settings'),
    path('config-settings/<int:config_id>/edit/', admin_login_required(edit_config_setting), name='edit_config_setting'),
    path('config-settings/<int:config_id>/delete/', admin_login_required(delete_config_setting), name='delete_config_setting'),
    path('config-settings/clear-cache/', admin_login_required(clear_config_cache), name='clear_config_cache'),

    # 支付网关管理
    path('payment/gateways/', admin_login_required(PaymentGatewayListView.as_view()), name='payment_gateway_list'),
    path('payment/gateways/add/', admin_login_required(PaymentGatewayCreateView.as_view()), name='payment_gateway_create'),
    path('payment/gateways/<int:pk>/edit/', admin_login_required(PaymentGatewayUpdateView.as_view()), name='payment_gateway_edit'),
    path('payment/gateways/<int:pk>/delete/', admin_login_required(PaymentGatewayDeleteView.as_view()), name='payment_gateway_delete'),
    path('payment/gateways/<int:pk>/config/', admin_login_required(PaymentGatewayConfigView.as_view()), name='payment_gateway_config'),
    path('payment/gateways/<int:pk>/test/', admin_login_required(PaymentGatewayTestView.as_view()), name='payment_gateway_test'),
    
    # 订阅计划管理
    path('payment/plans/', admin_login_required(SubscriptionPlanListView.as_view()), name='subscription_plan_list'),
    path('payment/plans/add/', admin_login_required(SubscriptionPlanCreateView.as_view()), name='subscription_plan_create'),
    path('payment/plans/<int:pk>/edit/', admin_login_required(SubscriptionPlanUpdateView.as_view()), name='subscription_plan_edit'),
    path('payment/plans/<int:pk>/delete/', admin_login_required(SubscriptionPlanDeleteView.as_view()), name='subscription_plan_delete'),
    
    # 会员订阅管理
    path('payment/subscriptions/', admin_login_required(SubscriptionListView.as_view()), name='subscription_list'),
    path('payment/subscriptions/<int:pk>/', admin_login_required(SubscriptionDetailView.as_view()), name='subscription_detail'),
    path('payment/subscriptions/<int:pk>/edit/', admin_login_required(SubscriptionUpdateView.as_view()), name='subscription_edit'),
]