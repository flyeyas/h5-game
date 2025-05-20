from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from datetime import timedelta, datetime
import json

from .models import Game, Category, UserProfile, Membership, Advertisement, GameHistory


def is_admin(user):
    """检查用户是否是管理员"""
    return user.is_authenticated and user.is_staff


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminDashboardView(TemplateView):
    """管理员仪表盘视图"""
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 统计数据
        context['total_games'] = Game.objects.count()
        context['total_users'] = User.objects.count()
        context['premium_members'] = UserProfile.objects.exclude(membership=None).count()
        context['total_views'] = Game.objects.aggregate(Sum('view_count'))['view_count__sum'] or 0
        
        # 最近添加的游戏
        context['recent_games'] = Game.objects.order_by('-created_at')[:5]
        
        # 最近注册的用户
        context['recent_users'] = UserProfile.objects.select_related('user', 'membership').order_by('-created_at')[:5]
        
        # 游戏访问统计图表数据
        # 获取过去30天的数据
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # 按日期分组统计游戏访问记录
        daily_views = GameHistory.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('created_at__date').annotate(
            count=Count('id')
        ).order_by('created_at__date')
        
        # 准备图表数据
        dates = [(start_date + timedelta(days=i)).date() for i in range(31)]
        views_count = [0] * 31
        
        # 填充实际数据
        date_dict = {item['created_at__date']: item['count'] for item in daily_views}
        for i, date in enumerate(dates):
            if date in date_dict:
                views_count[i] = date_dict[date]
        
        # 转换为JSON格式
        context['chart_labels'] = json.dumps([date.strftime('%b %d') for date in dates])
        context['chart_data'] = json.dumps(views_count)
        
        return context


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminGameListView(ListView):
    """管理员游戏列表视图"""
    model = Game
    template_name = 'admin/game_list.html'
    context_object_name = 'games'
    paginate_by = 10
    ordering = ['-created_at']


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminGameCreateView(CreateView):
    """管理员创建游戏视图"""
    model = Game
    template_name = 'admin/game_form.html'
    fields = ['title', 'slug', 'description', 'iframe_url', 'thumbnail', 'categories', 'is_featured', 'is_active']
    success_url = reverse_lazy('games:admin_game_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Game')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Game created successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminGameUpdateView(UpdateView):
    """管理员更新游戏视图"""
    model = Game
    template_name = 'admin/game_form.html'
    fields = ['title', 'slug', 'description', 'iframe_url', 'thumbnail', 'categories', 'is_featured', 'is_active']
    success_url = reverse_lazy('games:admin_game_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Game')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Game updated successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminGameDeleteView(DeleteView):
    """管理员删除游戏视图"""
    model = Game
    template_name = 'admin/game_confirm_delete.html'
    success_url = reverse_lazy('games:admin_game_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Game deleted successfully.'))
        return super().delete(request, *args, **kwargs)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminCategoryListView(ListView):
    """管理员分类列表视图"""
    model = Category
    template_name = 'admin/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10
    ordering = ['order', 'name']


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminCategoryCreateView(CreateView):
    """管理员创建分类视图"""
    model = Category
    template_name = 'admin/category_form.html'
    fields = ['name', 'slug', 'description', 'parent', 'image', 'order']
    success_url = reverse_lazy('games:admin_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Category')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Category created successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminCategoryUpdateView(UpdateView):
    """管理员更新分类视图"""
    model = Category
    template_name = 'admin/category_form.html'
    fields = ['name', 'slug', 'description', 'parent', 'image', 'order']
    success_url = reverse_lazy('games:admin_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Category')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Category updated successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminCategoryDeleteView(DeleteView):
    """管理员删除分类视图"""
    model = Category
    template_name = 'admin/category_confirm_delete.html'
    success_url = reverse_lazy('games:admin_category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Category deleted successfully.'))
        return super().delete(request, *args, **kwargs)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminUserListView(ListView):
    """管理员用户列表视图"""
    model = UserProfile
    template_name = 'admin/user_list.html'
    context_object_name = 'profiles'
    paginate_by = 10
    
    def get_queryset(self):
        return UserProfile.objects.select_related('user', 'membership').order_by('-created_at')


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminUserDetailView(DetailView):
    """管理员用户详情视图"""
    model = UserProfile
    template_name = 'admin/user_detail.html'
    context_object_name = 'profile'
    
    def get_object(self):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        return get_object_or_404(UserProfile, user=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        
        # 获取用户收藏的游戏和游戏历史
        context['favorite_games'] = self.object.favorite_games.all()
        context['game_history'] = GameHistory.objects.filter(user_id=user_id).select_related('game').order_by('-created_at')[:10]
        
        # 计算总游戏时间
        total_play_time = GameHistory.objects.filter(user_id=user_id).aggregate(Sum('duration'))
        context['total_play_time'] = total_play_time['duration__sum'] or 0
        
        # 计算活跃度分数 (基于游戏历史记录和收藏)
        activity_score = (context['game_history'].count() * 5) + (context['favorite_games'].count() * 2)
        context['activity_score'] = activity_score
        
        # 生成过去30天的活跃度数据
        activity_data = []
        activity_labels = []
        
        for i in range(30, 0, -1):
            date = timezone.now().date() - timedelta(days=i)
            next_date = date + timedelta(days=1)
            # 计算当天的游戏历史记录数
            daily_count = GameHistory.objects.filter(
                user_id=user_id,
                created_at__gte=date,
                created_at__lt=next_date
            ).count()
            
            # 简单的活跃度计算：每个游戏历史记录5分
            daily_score = daily_count * 5
            activity_data.append(daily_score)
            activity_labels.append(date.strftime('%m-%d'))
        
        context['activity_data'] = json.dumps(activity_data)
        context['activity_labels'] = json.dumps(activity_labels)
        
        # 添加当前时间和会员列表
        context['now'] = timezone.now()
        context['memberships'] = Membership.objects.filter(is_active=True).order_by('price')
        
        return context


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminMembershipListView(ListView):
    """管理员会员等级列表视图"""
    model = Membership
    template_name = 'admin/membership_list.html'
    context_object_name = 'memberships'
    ordering = ['price']


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminMembershipCreateView(CreateView):
    """管理员创建会员等级视图"""
    model = Membership
    template_name = 'admin/membership_form.html'
    fields = ['name', 'slug', 'level', 'price', 'duration_days', 'description', 'is_active']
    success_url = reverse_lazy('games:admin_membership_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Membership')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Membership created successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminMembershipUpdateView(UpdateView):
    """管理员更新会员等级视图"""


@user_passes_test(is_admin)
def admin_update_membership(request, user_id):
    """管理员更新用户会员资格"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': _('Invalid request method')})
    
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    
    membership_id = request.POST.get('membership_id')
    expiry_date = request.POST.get('expiry_date')
    
    try:
        # 如果选择了会员类型
        if membership_id:
            membership = get_object_or_404(Membership, id=membership_id)
            profile.membership = membership
            
            # 如果提供了过期日期，使用它；否则根据会员持续时间计算
            if expiry_date:
                profile.membership_expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            else:
                profile.membership_expiry = timezone.now().date() + timedelta(days=membership.duration_days)
        else:
            # 移除会员资格
            profile.membership = None
            profile.membership_expiry = None
        
        profile.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@user_passes_test(is_admin)
def admin_toggle_user_status(request, user_id):
    """管理员切换用户状态（激活/停用）"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': _('Invalid request method')})
    
    try:
        data = json.loads(request.body)
        active = data.get('active', False)
        
        user = get_object_or_404(User, id=user_id)
        user.is_active = active
        user.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminMembershipUpdateView(UpdateView):
    """管理员更新会员等级视图"""
    model = Membership
    template_name = 'admin/membership_form.html'
    fields = ['name', 'slug', 'level', 'price', 'duration_days', 'description', 'is_active']
    success_url = reverse_lazy('games:admin_membership_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Membership')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Membership updated successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminMembershipDeleteView(DeleteView):
    """管理员删除会员等级视图"""
    model = Membership
    template_name = 'admin/membership_confirm_delete.html'
    success_url = reverse_lazy('games:admin_membership_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Membership deleted successfully.'))
        return super().delete(request, *args, **kwargs)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminAdListView(ListView):
    """管理员广告列表视图"""
    model = Advertisement
    template_name = 'admin/ad_list.html'
    context_object_name = 'ads'
    paginate_by = 10
    ordering = ['-created_at']


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminAdCreateView(CreateView):
    """管理员创建广告视图"""
    model = Advertisement
    template_name = 'admin/ad_form.html'
    fields = ['name', 'position', 'image', 'url', 'html_code', 'is_active', 'start_date', 'end_date']
    success_url = reverse_lazy('games:admin_ad_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Advertisement')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Advertisement created successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminAdUpdateView(UpdateView):
    """管理员更新广告视图"""
    model = Advertisement
    template_name = 'admin/ad_form.html'
    fields = ['name', 'position', 'image', 'url', 'html_code', 'is_active', 'start_date', 'end_date']
    success_url = reverse_lazy('games:admin_ad_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Advertisement')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Advertisement updated successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminAdDeleteView(DeleteView):
    """管理员删除广告视图"""
    model = Advertisement
    template_name = 'admin/ad_confirm_delete.html'
    success_url = reverse_lazy('games:admin_ad_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Advertisement deleted successfully.'))
        return super().delete(request, *args, **kwargs)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminStatsView(TemplateView):
    """管理员统计视图"""
    template_name = 'admin/stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 处理日期范围选择
        date_range = self.request.GET.get('date_range', '30')
        context['date_range'] = date_range
        
        # 设置日期范围
        end_date = timezone.now()
        
        if date_range == 'custom':
            # 处理自定义日期范围
            try:
                start_date_str = self.request.GET.get('start_date')
                end_date_str = self.request.GET.get('end_date')
                
                if start_date_str and end_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                else:
                    # 默认为过去30天
                    start_date = end_date - timedelta(days=30)
            except ValueError:
                # 日期格式错误，使用默认值
                start_date = end_date - timedelta(days=30)
        else:
            # 根据选择的预设日期范围设置开始日期
            days = int(date_range)
            start_date = end_date - timedelta(days=days)
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # 计算上一个时间段，用于比较变化
        previous_period_length = (end_date - start_date).days
        previous_start_date = start_date - timedelta(days=previous_period_length)
        previous_end_date = start_date - timedelta(seconds=1)
        
        # 统计卡片数据
        # 1. 游戏总游玩次数
        current_games_played = GameHistory.objects.filter(created_at__range=(start_date, end_date)).count()
        previous_games_played = GameHistory.objects.filter(created_at__range=(previous_start_date, previous_end_date)).count()
        
        context['total_games_played'] = current_games_played
        context['games_played_change'] = self._calculate_percentage_change(current_games_played, previous_games_played)
        
        # 2. 新用户数量
        current_new_users = User.objects.filter(date_joined__range=(start_date, end_date)).count()
        previous_new_users = User.objects.filter(date_joined__range=(previous_start_date, previous_end_date)).count()
        
        context['new_users'] = current_new_users
        context['new_users_change'] = self._calculate_percentage_change(current_new_users, previous_new_users)
        
        # 3. 平均游戏时长（分钟）
        current_play_times = GameHistory.objects.filter(created_at__range=(start_date, end_date)).aggregate(avg_time=models.Avg('play_time'))
        previous_play_times = GameHistory.objects.filter(created_at__range=(previous_start_date, previous_end_date)).aggregate(avg_time=models.Avg('play_time'))
        
        current_avg_play_time = round((current_play_times['avg_time'] or 0) / 60, 1)  # 转换为分钟
        previous_avg_play_time = (previous_play_times['avg_time'] or 0) / 60
        
        context['avg_play_time'] = current_avg_play_time
        context['avg_play_time_change'] = self._calculate_percentage_change(current_avg_play_time, previous_avg_play_time)
        
        # 4. 广告点击次数
        current_ad_clicks = Advertisement.objects.filter(updated_at__range=(start_date, end_date)).aggregate(Sum('click_count'))['click_count__sum'] or 0
        previous_ad_clicks = Advertisement.objects.filter(updated_at__range=(previous_start_date, previous_end_date)).aggregate(Sum('click_count'))['click_count__sum'] or 0
        
        context['ad_clicks'] = current_ad_clicks
        context['ad_clicks_change'] = self._calculate_percentage_change(current_ad_clicks, previous_ad_clicks)
        
        # 游戏活跃度趋势图数据
        activity_data, activity_labels = self._get_activity_trend_data(start_date, end_date)
        context['activity_data'] = json.dumps(activity_data)
        context['activity_labels'] = json.dumps(activity_labels)
        
        # 用户增长图数据 - 会员分布
        free_users = User.objects.count() - UserProfile.objects.exclude(membership=None).count()
        basic_members = UserProfile.objects.filter(membership__level='basic').count()
        premium_members = UserProfile.objects.filter(membership__level='premium').count()
        
        context['user_distribution'] = json.dumps([free_users, basic_members, premium_members])
        
        # 热门游戏排行
        top_games = Game.objects.annotate(
            play_count=Count('play_history', filter=models.Q(play_history__created_at__range=(start_date, end_date))),
            avg_play_time=models.Avg('play_history__play_time', filter=models.Q(play_history__created_at__range=(start_date, end_date)))
        ).order_by('-play_count')[:10]
        
        # 转换平均游戏时长为分钟
        for game in top_games:
            game.avg_play_time = round((game.avg_play_time or 0) / 60, 1)
        
        context['top_games'] = top_games
        
        # 广告效果统计
        ads_performance = Advertisement.objects.annotate(
            view_count_period=models.Sum('view_count', filter=models.Q(updated_at__range=(start_date, end_date))),
            click_count_period=models.Sum('click_count', filter=models.Q(updated_at__range=(start_date, end_date)))
        ).order_by('-click_count_period')[:10]
        
        # 计算点击率 (CTR)
        for ad in ads_performance:
            ad.view_count = ad.view_count_period or 0
            ad.click_count = ad.click_count_period or 0
            ad.ctr = (ad.click_count / ad.view_count * 100) if ad.view_count > 0 else 0
        
        context['ads_performance'] = ads_performance
        
        # 收入统计图表数据
        revenue_data, revenue_labels = self._get_revenue_data(start_date, end_date)
        context['revenue_data'] = json.dumps(revenue_data)
        context['revenue_labels'] = json.dumps(revenue_labels)
        
        return context
    
    def _calculate_percentage_change(self, current, previous):
        """计算百分比变化"""
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    def _get_activity_trend_data(self, start_date, end_date):
        """获取游戏活跃度趋势数据"""
        days = (end_date - start_date).days + 1
        activity_data = []
        activity_labels = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            
            # 计算当天的游戏历史记录数
            daily_count = GameHistory.objects.filter(
                created_at__gte=current_date,
                created_at__lt=next_date
            ).count()
            
            activity_data.append(daily_count)
            activity_labels.append(current_date.strftime('%m-%d'))
        
        return activity_data, activity_labels
    
    def _get_revenue_data(self, start_date, end_date):
        """获取收入统计数据"""
        # 这里假设有一个订阅记录模型，如果没有，可以根据实际情况调整
        # 这里使用会员等级的价格和用户数量来模拟收入数据
        days = (end_date - start_date).days + 1
        revenue_data = []
        revenue_labels = []
        
        # 简化处理：按会员等级统计收入
        basic_revenue = UserProfile.objects.filter(
            membership__level='basic',
            membership_expiry__gte=start_date,
            membership_expiry__lte=end_date
        ).count() * 10  # 假设基础会员价格为10
        
        premium_revenue = UserProfile.objects.filter(
            membership__level='premium',
            membership_expiry__gte=start_date,
            membership_expiry__lte=end_date
        ).count() * 30  # 假设高级会员价格为30
        
        # 简化为两个数据点：基础会员和高级会员收入
        revenue_data = [basic_revenue, premium_revenue]
        revenue_labels = [_('Basic Membership'), _('Premium Membership')]
        
        return revenue_data, revenue_labels


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminSettingsView(TemplateView):
    """管理员设置视图"""
    template_name = 'admin/settings.html'