from django.urls import path
from . import views
from .views_category import CategoryDetailView
from .views_auth import (
    RegisterView, LoginView, logout_view, 
    CustomPasswordResetView, PasswordResetDoneView,
    CustomPasswordResetConfirmView, PasswordResetCompleteView
)
from .views_membership import (
    MembershipListView, MembershipDetailView, 
    subscribe_membership, MembershipHistoryView
)
from .views_payment import (
    process_payment, PaymentMethodSelectionView, PaymentProcessView, 
    PaymentSuccessView, PaymentFailedView, retry_payment, 
    PaymentHistoryView, PaymentInvoiceDetailView, download_invoice,
    change_payment_method
)
from .views_payment_callback import payment_callback, payment_notification
from .views_ad import ad_click
from .views_admin import (
    AdminDashboardView, AdminGameListView, AdminGameCreateView, AdminGameUpdateView, AdminGameDeleteView,
    AdminCategoryListView, AdminCategoryCreateView, AdminCategoryUpdateView, AdminCategoryDeleteView,
    AdminUserListView, AdminUserDetailView, AdminMembershipListView, AdminMembershipCreateView,
    AdminMembershipUpdateView, AdminMembershipDeleteView, AdminAdListView, AdminAdCreateView,
    AdminAdUpdateView, AdminAdDeleteView, AdminStatsView, AdminSettingsView, admin_update_membership, admin_toggle_user_status
)
from .views_payment_admin import (
    AdminPaymentListView, admin_payment_confirm, admin_payment_reject,
    AdminPaymentMethodListView, AdminPaymentMethodCreateView, 
    AdminPaymentMethodUpdateView, AdminPaymentMethodDeleteView, PaymentExportView, PaymentStatisticsExportView,
    PaymentTemplateListView, PaymentTemplateCreateView, PaymentTemplateUpdateView, PaymentTemplateDeleteView,
    admin_payment_template_preview, admin_payment_template_duplicate, admin_payment_template_toggle_status, admin_payment_template_restore_defaults
)
from .views_menu_settings import (
    MenuListView, MenuCreateView, MenuUpdateView, MenuDeleteView,
    MenuItemListView, MenuItemCreateView, MenuItemUpdateView, MenuItemDeleteView,
    website_settings, language_management, translation_management
)
from . import views_payment, payment_callbacks

app_name = 'games'

urlpatterns = [
    # 首页
    path('', views.HomeView.as_view(), name='home'),
    
    # 游戏列表
    path('games/', views.GameListView.as_view(), name='game_list'),
    path('category/<slug:category_slug>/games/', views.GameListView.as_view(), name='category_games'),
    
    # 游戏详情
    path('game/<slug:game_slug>/', views.GameDetailView.as_view(), name='game_detail'),
    
    # 分类相关
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:category_slug>/', CategoryDetailView.as_view(), name='category_detail'),
    
    # 用户相关
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('favorite/toggle/<int:game_id>/', views.toggle_favorite, name='toggle_favorite'),
    
    # 认证相关
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # 会员订阅相关
    path('subscription/', MembershipListView.as_view(), name='subscription'),
    path('membership/<slug:membership_slug>/', MembershipDetailView.as_view(), name='membership_detail'),
    path('subscribe/<int:membership_id>/', subscribe_membership, name='subscribe_membership'),
    path('membership-history/', MembershipHistoryView.as_view(), name='membership_history'),
    path('process-payment/<int:membership_id>/', process_payment, name='process_payment'),
    path('payment/method/<int:payment_id>/', PaymentMethodSelectionView.as_view(), name='payment_method_selection'),
    path('payment/process/<int:payment_id>/', PaymentProcessView.as_view(), name='payment_process'),
    path('payment/success/<int:payment_id>/', PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/failed/<int:payment_id>/', PaymentFailedView.as_view(), name='payment_failed'),
    path('payment/retry/<int:payment_id>/', retry_payment, name='retry_payment'),
    path('payment/change-method/<int:payment_id>/', change_payment_method, name='change_payment_method'),
    path('payment/history/', PaymentHistoryView.as_view(), name='payment_history'),
    path('payment/invoice/<int:invoice_id>/', PaymentInvoiceDetailView.as_view(), name='payment_invoice_detail'),
    path('payment/invoice/<int:invoice_id>/download/', download_invoice, name='download_invoice'),
    path('payment/callback/<int:payment_id>/', payment_callback, name='payment_callback'),
    path('payment/notification/', payment_notification, name='payment_notification'),
    
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
    
    # 用户管理
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:user_id>/update-membership/', admin_update_membership, name='admin_update_membership'),
    path('admin/users/<int:user_id>/toggle-status/', admin_toggle_user_status, name='admin_toggle_user_status'),
    
    # 会员管理
    path('admin/memberships/', AdminMembershipListView.as_view(), name='admin_membership_list'),
    path('admin/memberships/create/', AdminMembershipCreateView.as_view(), name='admin_membership_create'),
    path('admin/memberships/<int:pk>/edit/', AdminMembershipUpdateView.as_view(), name='admin_membership_edit'),
    path('admin/memberships/<int:pk>/delete/', AdminMembershipDeleteView.as_view(), name='admin_membership_delete'),
    
    # 广告管理
    path('admin/ads/', AdminAdListView.as_view(), name='admin_ad_list'),
    path('admin/ads/create/', AdminAdCreateView.as_view(), name='admin_ad_create'),
    path('admin/ads/<int:pk>/edit/', AdminAdUpdateView.as_view(), name='admin_ad_edit'),
    path('admin/ads/<int:pk>/delete/', AdminAdDeleteView.as_view(), name='admin_ad_delete'),
    
    # 支付管理
    path('admin/payments/', AdminPaymentListView.as_view(), name='admin_payment_list'),
    path('admin/payments/<int:payment_id>/confirm/', admin_payment_confirm, name='admin_payment_confirm'),
    path('admin/payments/<int:payment_id>/reject/', admin_payment_reject, name='admin_payment_reject'),
    path('admin/payment-methods/', AdminPaymentMethodListView.as_view(), name='admin_payment_method_list'),
    path('admin/payment-methods/create/', AdminPaymentMethodCreateView.as_view(), name='admin_payment_method_create'),
    path('admin/payment-methods/<int:pk>/edit/', AdminPaymentMethodUpdateView.as_view(), name='admin_payment_method_edit'),
    path('admin/payment-methods/<int:pk>/delete/', AdminPaymentMethodDeleteView.as_view(), name='admin_payment_method_delete'),
    
    # 菜单管理
    path('admin/menus/', MenuListView.as_view(), name='admin_menu_list'),
    path('admin/menus/create/', MenuCreateView.as_view(), name='admin_menu_create'),
    path('admin/menus/<int:pk>/edit/', MenuUpdateView.as_view(), name='admin_menu_edit'),
    path('admin/menus/<int:pk>/delete/', MenuDeleteView.as_view(), name='admin_menu_delete'),
    path('admin/menus/<int:menu_id>/items/', MenuItemListView.as_view(), name='admin_menu_items'),
    path('admin/menus/<int:menu_id>/items/create/', MenuItemCreateView.as_view(), name='admin_menu_item_create'),
    path('admin/menu-items/<int:pk>/edit/', MenuItemUpdateView.as_view(), name='admin_menu_item_edit'),
    path('admin/menu-items/<int:pk>/delete/', MenuItemDeleteView.as_view(), name='admin_menu_item_delete'),
    
    # 网站设置
    path('admin/website-settings/', website_settings, name='admin_website_settings'),
    path('admin/language-management/', language_management, name='admin_language_management'),
    
    # 统计和设置
    path('admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('admin/settings/', AdminSettingsView.as_view(), name='admin_settings'),
    
    # 翻译管理
    path('admin/translation-management/', translation_management, name='admin_translation_management'),
    
    # 支付回调URL
    path('payment/callback/<str:payment_method_code>/',
         payment_callbacks.payment_callback,
         name='payment_callback'),
    
    # 支付数据导出URL
    path('admin/payments/export/', PaymentExportView.as_view(), name='payment_export'),
    path('admin/payments/statistics/export/', PaymentStatisticsExportView.as_view(), name='payment_statistics_export'),

    # 支付模板管理URL
    path('admin/payment-templates/', PaymentTemplateListView.as_view(), name='admin_payment_template_list'),
    path('admin/payment-templates/create/', PaymentTemplateCreateView.as_view(), name='admin_payment_template_create'),
    path('admin/payment-templates/<int:pk>/edit/', PaymentTemplateUpdateView.as_view(), name='admin_payment_template_edit'),
    path('admin/payment-templates/<int:pk>/delete/', PaymentTemplateDeleteView.as_view(), name='admin_payment_template_delete'),
    path('admin/payment-templates/<int:template_id>/preview/', admin_payment_template_preview, name='admin_payment_template_preview'),
    path('admin/payment-templates/<int:template_id>/duplicate/', admin_payment_template_duplicate, name='admin_payment_template_duplicate'),
    path('admin/payment-templates/<int:template_id>/toggle-status/', admin_payment_template_toggle_status, name='admin_payment_template_toggle_status'),
    path('admin/payment-templates/restore-defaults/', admin_payment_template_restore_defaults, name='admin_payment_template_restore_defaults'),
]