from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
import csv
from datetime import datetime, timedelta
import json

from .models import Game, Category, Advertisement

# 检查用户是否是管理员的函数
def is_admin(user):
    return user.is_authenticated and user.is_superuser


# 管理员仪表盘视图
class AdminDashboardView(UserPassesTestMixin, TemplateView):
    template_name = 'admin/dashboard.html'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 基础统计数据
        context['total_games'] = Game.objects.count()
        context['total_categories'] = Category.objects.count()
        context['total_views'] = Game.objects.aggregate(Sum('view_count'))['view_count__sum'] or 0
        
        # 最近添加的游戏
        context['recent_games'] = Game.objects.order_by('-created_at')[:5]
        
        # 最受欢迎的游戏
        context['popular_games'] = Game.objects.order_by('-view_count')[:5]
        
        return context


# 游戏管理视图
class AdminGameListView(UserPassesTestMixin, ListView):
    template_name = 'admin/game_list.html'
    model = Game
    context_object_name = 'games'
    paginate_by = 10
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        queryset = Game.objects.all()
        
        # 搜索过滤
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
            
        # 分类过滤
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
            
        # 状态过滤
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        # 排序
        sort = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_sort'] = self.request.GET.get('sort', '-created_at')
        return context


class AdminGameCreateView(UserPassesTestMixin, CreateView):
    model = Game
    template_name = 'admin/game_form.html'
    fields = ['title', 'slug', 'description', 'iframe_url', 'thumbnail', 'categories', 'is_featured', 'is_active']
    success_url = reverse_lazy('games:admin_game_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Game')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Game created successfully.'))
        return response


class AdminGameUpdateView(UserPassesTestMixin, UpdateView):
    model = Game
    template_name = 'admin/game_form.html'
    fields = ['title', 'slug', 'description', 'iframe_url', 'thumbnail', 'categories', 'is_featured', 'is_active']
    success_url = reverse_lazy('games:admin_game_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Game')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Game updated successfully.'))
        return response


class AdminGameDeleteView(UserPassesTestMixin, DeleteView):
    model = Game
    template_name = 'admin/game_confirm_delete.html'
    success_url = reverse_lazy('games:admin_game_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Game deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# 分类管理视图
class AdminCategoryListView(UserPassesTestMixin, ListView):
    template_name = 'admin/category_list.html'
    model = Category
    context_object_name = 'categories'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        return Category.objects.all().order_by('order', 'name')


class AdminCategoryCreateView(UserPassesTestMixin, CreateView):
    model = Category
    template_name = 'admin/category_form.html'
    fields = ['name', 'slug', 'description', 'parent', 'image', 'icon_class', 'order', 'is_active']
    success_url = reverse_lazy('games:admin_category_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Category')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Category created successfully.'))
        return response


class AdminCategoryUpdateView(UserPassesTestMixin, UpdateView):
    model = Category
    template_name = 'admin/category_form.html'
    fields = ['name', 'slug', 'description', 'parent', 'image', 'icon_class', 'order', 'is_active']
    success_url = reverse_lazy('games:admin_category_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Category')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Category updated successfully.'))
        return response


class AdminCategoryDeleteView(UserPassesTestMixin, DeleteView):
    model = Category
    template_name = 'admin/category_confirm_delete.html'
    success_url = reverse_lazy('games:admin_category_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Category deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# 用户管理视图已移除


# 用户详情视图和用户状态切换功能已移除


# 广告管理视图
class AdminAdListView(UserPassesTestMixin, ListView):
    template_name = 'admin/ad_list.html'
    model = Advertisement
    context_object_name = 'ads'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        return Advertisement.objects.all().order_by('-created_at')


class AdminAdCreateView(UserPassesTestMixin, CreateView):
    model = Advertisement
    template_name = 'admin/ad_form.html'
    fields = ['name', 'position', 'image', 'url', 'html_code', 'is_active', 'start_date', 'end_date']
    success_url = reverse_lazy('games:admin_ad_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Advertisement')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Advertisement created successfully.'))
        return response


class AdminAdUpdateView(UserPassesTestMixin, UpdateView):
    model = Advertisement
    template_name = 'admin/ad_form.html'
    fields = ['name', 'position', 'image', 'url', 'html_code', 'is_active', 'start_date', 'end_date']
    success_url = reverse_lazy('games:admin_ad_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Advertisement')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Advertisement updated successfully.'))
        return response


class AdminAdDeleteView(UserPassesTestMixin, DeleteView):
    model = Advertisement
    template_name = 'admin/ad_confirm_delete.html'
    success_url = reverse_lazy('games:admin_ad_list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Advertisement deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# 统计视图
class AdminStatsView(UserPassesTestMixin, TemplateView):
    template_name = 'admin/stats.html'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取时间范围
        end_date = timezone.now().date()
        start_date = self.request.GET.get('start_date')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # 游戏浏览统计
        game_views = []
        popular_games = Game.objects.filter(
            play_history__played_at__date__gte=start_date,
            play_history__played_at__date__lte=end_date
        ).annotate(play_count=Count('play_history')).order_by('-play_count')[:10]
        
        for game in popular_games:
            game_views.append({
                'name': game.title,
                'count': game.play_count
            })
        
        context['game_views'] = json.dumps(game_views)
        
        # 用户统计
        new_users = []
        date_range = (end_date - start_date).days + 1
        
        for i in range(date_range):
            current_date = start_date + timedelta(days=i)
            count = User.objects.filter(
                date_joined__date=current_date
            ).count()
            
            new_users.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        context['new_users'] = json.dumps(new_users)
        
        # 用户类型分布
        free_users = User.objects.count()
        
        user_types = [
            {'name': _('Free Users'), 'count': free_users},
        ]
        
        context['user_types'] = json.dumps(user_types)
        
        return context


# 设置视图
class AdminSettingsView(UserPassesTestMixin, TemplateView):
    template_name = 'admin/settings.html'
    
    def test_func(self):
        return is_admin(self.request.user)