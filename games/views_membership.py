from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Membership, UserProfile


class MembershipListView(ListView):
    """会员等级列表视图"""
    model = Membership
    template_name = 'games/membership/subscription.html'
    context_object_name = 'memberships'
    
    def get_queryset(self):
        return Membership.objects.filter(is_active=True).order_by('price')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取当前用户的会员信息
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                context['current_membership'] = profile.membership
                context['membership_expiry'] = profile.membership_expiry
            except UserProfile.DoesNotExist:
                pass
        
        return context


@method_decorator(login_required, name='dispatch')
class MembershipDetailView(DetailView):
    """会员等级详情视图"""
    model = Membership
    template_name = 'games/membership/membership_detail.html'
    context_object_name = 'membership'
    slug_url_kwarg = 'membership_slug'


@login_required
def subscribe_membership(request, membership_id):
    """订阅会员视图"""
    membership = get_object_or_404(Membership, id=membership_id, is_active=True)
    
    # 获取用户资料
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    # 设置会员等级和到期时间
    profile.membership = membership
    
    # 如果已经有会员，则延长时间，否则从当前时间开始计算
    if profile.membership_expiry and profile.membership_expiry > timezone.now():
        profile.membership_expiry += timedelta(days=membership.duration_days)
    else:
        profile.membership_expiry = timezone.now() + timedelta(days=membership.duration_days)
    
    profile.save()
    
    messages.success(request, _('You have successfully subscribed to {} membership!').format(membership.name))
    
    # 这里应该有支付处理逻辑，暂时简化为直接订阅成功
    
    return redirect('games:user_profile')


@method_decorator(login_required, name='dispatch')
class MembershipHistoryView(TemplateView):
    """会员历史记录视图"""
    template_name = 'games/membership/membership_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取用户资料
        try:
            profile = self.request.user.profile
            context['profile'] = profile
            context['current_membership'] = profile.membership
            context['membership_expiry'] = profile.membership_expiry
            context['now'] = timezone.now()  # 添加当前时间到上下文
        except UserProfile.DoesNotExist:
            pass
        
        return context