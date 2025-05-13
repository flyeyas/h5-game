from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum, Count, Q
import logging
from django.conf import settings
from games.models import Game
from django.contrib.auth.views import LoginView
from django.contrib.auth import login as auth_login, logout as auth_logout

# 获取日志记录器
logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """管理后台首页"""
    logger.info(f"用户 {request.user.username} 访问了管理后台首页")
    
    try:
        # 获取游戏统计数据
        game_stats = {
            'total_games': Game.objects.count(),
            'active_games': Game.objects.filter(status='online').count(),
            'total_plays': Game.objects.aggregate(total=Sum('play_count'))['total'] or 0,
            'total_favorites': Game.objects.filter(front_favorited_by__isnull=False).distinct().count(),
        }
        
        context = {
            'title': _('管理后台首页'),
            'game_stats': game_stats,
        }
        
        return render(request, 'admin/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"渲染管理后台首页时发生错误: {str(e)}")
        messages.error(request, _('加载管理后台首页时发生错误'))
        return redirect('admin_panel:dashboard')

# 管理员账号相关视图已移至 admin_user_views.py

# 菜单管理相关视图已移至 menu_views.py

class AdminLoginView(LoginView):
    """
    管理员登录视图
    使用Django默认认证后端
    """
    template_name = 'admin_panel/login.html'
    
    def form_valid(self, form):
        """使用Django默认的登录流程"""
        # 使用Django默认的login处理
        auth_login(self.request, form.get_user())
        
        # 记录登录信息
        logger = logging.getLogger('admin')
        logger.info(f"管理员登录成功: 用户={form.get_user().username}")
        
        # 重定向到成功URL
        return redirect(self.get_success_url())
        
    def get_success_url(self):
        return reverse('admin_panel:dashboard')

def admin_logout_view(request):
    """管理员登出视图，使用Django默认的登出流程"""
    # 使用Django默认的logout函数
    auth_logout(request)
    
    # 记录登出信息
    logger = logging.getLogger('admin')
    logger.info("管理员登出")
    
    # 重定向到登录页
    return redirect('admin_panel:admin_login')
