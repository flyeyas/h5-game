from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from . import views
from .ajax import (
    favorite_toggle, favorite_toggle_api, comment_like, comment_submit, game_rating_submit,
    log_game_play, get_game_detail, get_game_comments, send_password_reset_code,
    verify_reset_code, reset_password, login_ajax, game_history_ajax,
    delete_history_ajax, clear_history_ajax, clear_all_history_ajax
)
from .views import (
    HomeView, GameListView, GameDetailView, GameDetailByIdView,
    CategoryDetailView, HotGamesView, NewGamesView, GameSearchView,
    ProfileHistoryView, ProfileSettingsView, ProfileMembershipView,
    UpdateProfileView, ChangePasswordView, 
    DeleteAccountView, UserProfileView,
    FrontendLoginView, register, MembershipPlansView, FavoritesApiView,
    GameHistoryApiView, SocialConnectView, SendEmailVerificationView,
    UpdateEmailView, RegisterVerificationCodeView, RegisterApiView,
    ForgotPasswordView
)
from django.contrib.auth.views import LogoutView
from django.views.generic.base import RedirectView
from . import payment_views

# 应用命名空间
app_name = 'games'

urlpatterns = [
    # 首页
    path('', HomeView.as_view(), name='home'),
    
    # 游戏相关页面
    path('games/', GameListView.as_view(), name='game_list'),
    path('games/category/<slug:category_slug>/', GameListView.as_view(), name='game_list_by_category'),
    path('games/<int:game_id>/', GameDetailByIdView.as_view(), name='game_detail_by_id'),
    path('games/<slug:game_slug>/', GameDetailView.as_view(), name='game_detail'),
    path('game/<int:game_id>/', GameDetailByIdView.as_view(), name='game_detail_by_id_alt'),
    path('hot-games/', HotGamesView.as_view(), name='hot_games'),
    path('new-games/', NewGamesView.as_view(), name='new_games'),
    path('search/', GameSearchView.as_view(), name='game_search'),
    
    # 分类与标签
    path('categories/<slug:category_slug>/', CategoryDetailView.as_view(), name='category_detail'),
    path('categories/', GameListView.as_view(), name='game_categories'),
    
    # 登录路径重定向
    path('login/', RedirectView.as_view(pattern_name='games:login', permanent=False), name='login_redirect'),
    
    # 认证相关 - 使用Django标准视图
    path('accounts/login/', FrontendLoginView.as_view(template_name='games/registration/login.html'), name='login'),
    path('accounts/logout/', LogoutView.as_view(next_page='/', http_method_names=['get', 'post']), name='logout'),
    path('accounts/register/', register, name='register'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='games/registration/password_reset_form.html',
        email_template_name='games/registration/password_reset_email.html',
        success_url='/accounts/password_reset/done/'
    ), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='games/registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='games/registration/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='games/registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Ajax登录API
    path('api/login/', login_ajax, name='login_ajax'),
    path('api/register/send-code/', RegisterVerificationCodeView.as_view(), name='register_send_code'),
    path('api/register/', RegisterApiView.as_view(), name='register_api'),
    
    # 用户个人中心
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/history/', ProfileHistoryView.as_view(), name='profile_history'),
    path('profile/settings/', ProfileSettingsView.as_view(), name='profile_settings'),
    path('profile/membership/', ProfileMembershipView.as_view(), name='profile_membership'),
    
    # 用户资料更新API
    path('profile/update/', UpdateProfileView.as_view(), name='update_profile'),
    path('profile/update-email/', UpdateEmailView.as_view(), name='update_email'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/delete/', DeleteAccountView.as_view(), name='delete_account'),
    path('profile/social-connect/', SocialConnectView.as_view(), name='social_connect'),
    path('profile/send-verification/', SendEmailVerificationView.as_view(), name='send_email_verification'),
    
    # 游戏操作API
    path('api/game/<int:game_id>/favorite/', favorite_toggle, name='favorite_toggle'),
    path('api/game/<int:game_id>/play/', log_game_play, name='log_game_play'),
    path('api/game/<int:game_id>/detail/', get_game_detail, name='get_game_detail'),
    path('api/game/<int:game_id>/comments/', get_game_comments, name='get_game_comments'),
    path('api/comment/submit/', comment_submit, name='comment_submit'),
    path('api/comment/<int:comment_id>/like/', comment_like, name='comment_like'),
    path('api/favorites/', FavoritesApiView.as_view(), name='favorites_api'),
    path('api/history/', GameHistoryApiView.as_view(), name='history_api'),
    path('api/history/<int:history_id>/delete/', GameHistoryApiView.as_view(), name='history_delete_api'),
    path('api/history/clear/', GameHistoryApiView.as_view(), name='history_clear_api'),
    
    # 密码重置API
    path('api/password/reset/send-code/', send_password_reset_code, name='send_password_reset_code'),
    path('api/password/reset/verify-code/', verify_reset_code, name='verify_reset_code'),
    path('api/password/reset/submit/', reset_password, name='reset_password'),
    
    # 静态页面
    path('about/', TemplateView.as_view(template_name='games/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='games/contact.html'), name='contact'),
    path('terms/', TemplateView.as_view(template_name='games/terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='games/privacy.html'), name='privacy'),
    path('help/', TemplateView.as_view(template_name='games/help.html'), name='help'),
    
    # 会员计划
    path('membership-plans/', MembershipPlansView.as_view(), name='membership_plans'),
    
    # 游戏历史AJAX接口
    path('ajax/game-history/', game_history_ajax, name='game_history_ajax'),
    path('ajax/delete-history/<int:history_id>/', delete_history_ajax, name='delete_history_ajax'),
    path('ajax/clear-history/', clear_history_ajax, name='clear_history_ajax'),
    
    # 游戏收藏AJAX接口 - 兼容旧版前端调用
    path('ajax/favorite-toggle/<int:game_id>/', favorite_toggle, name='favorite_toggle_alt'),
]

# AJAX接口
urlpatterns += [
    path('ajax/game/<int:game_id>/', get_game_detail, name='ajax_game_detail'),
    path('ajax/favorite/toggle/', favorite_toggle, name='ajax_favorite_toggle'),
    path('api/favorite/toggle/', favorite_toggle_api, name='api_favorite_toggle'),
    path('ajax/history/', game_history_ajax, name='ajax_history'),
    path('ajax/history/delete/', delete_history_ajax, name='ajax_delete_history'),
    path('ajax/history/clear-all/', clear_all_history_ajax, name='ajax_clear_all_history'),
]

# 支付相关URL
urlpatterns += [
    path('membership/plans/', payment_views.subscription_plans, name='subscription_plans'),
    path('membership/checkout/<int:plan_id>/', payment_views.checkout, name='checkout'),
    path('membership/payment/<int:plan_id>/<int:gateway_id>/', payment_views.payment_method, name='payment_method'),
    path('membership/success/', payment_views.payment_success, name='payment_success'),
    path('membership/cancel/', payment_views.payment_cancel, name='payment_cancel'),
    path('membership/error/', payment_views.payment_error, name='payment_error'),
    
    # 各支付网关处理URL
    path('membership/paypal/<int:transaction_id>/', payment_views.paypal_payment, name='paypal_payment'),
    path('payments/paypal/webhook/', payment_views.paypal_webhook, name='paypal_webhook'),
] 