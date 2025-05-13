import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Case, When, IntegerField, F, OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from admin_panel.admin_site import admin_login_required
from admin_panel.models import AdminLog
from games.models import UserProfile
from core.api_utils import api_response

logger = logging.getLogger('admin')

# 获取Django默认用户模型
User = get_user_model()

# 管理员操作日志记录
def admin_operate_log(request, action_description):
    """记录管理员操作日志"""
    AdminLog.objects.create(
        admin=request.user,
        action=action_description,
        ip_address=request.META.get('REMOTE_ADDR', '')
    )

@login_required
@admin_login_required
def list_front_users(request):
    """前台用户列表页面"""
    logger.info("访问前台用户列表页面")
    
    # 获取查询参数
    query = request.GET.get('q', '')
    is_active_filter = request.GET.get('is_active', '')
    is_member_filter = request.GET.get('is_member', '')
    member_type_filter = request.GET.get('member_type', '')
    
    # 分页参数
    page_size = 10  # 每页显示数量
    page_number = request.GET.get('page', '1')
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
    except (ValueError, TypeError):
        page_number = 1
        logger.warning("无效的页码参数: %s, 使用默认页码1", request.GET.get('page'))
    
    # 计算数据库分页的offset
    offset = (page_number - 1) * page_size
    
    # 获取前台用户列表 - 从auth_user和profile联表查询
    # 排除is_staff=True的用户，因为他们是管理员用户
    query_set = User.objects.filter(is_staff=False).select_related('profile')
    
    # 应用过滤条件
    if query:
        query_set = query_set.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query)
        )
    
    if is_active_filter != '':
        is_active = is_active_filter.lower() == 'true'
        query_set = query_set.filter(is_active=is_active)
    
    if is_member_filter != '':
        is_member = is_member_filter.lower() == 'true'
        query_set = query_set.filter(profile__is_member=is_member)
    
    if member_type_filter:
        query_set = query_set.filter(profile__member_type=member_type_filter)
    
    # 按用户创建时间降序排序
    query_set = query_set.order_by('-date_joined')
    
    # 获取总记录数，用于分页
    total_count = query_set.count()
    total_pages = (total_count + page_size - 1) // page_size  # 向上取整计算总页数
    
    # 使用 SQL LIMIT/OFFSET 进行数据库级分页
    user_list = query_set[offset:offset + page_size]
    logger.info("执行数据库级分页查询: offset=%s, limit=%s", offset, page_size)
    
    # 创建基础查询用于统计
    base_stats_query = User.objects.filter(is_staff=False)
    
    # 使用聚合查询来减少数据库请求次数 - 统计活跃和非活跃用户
    current_time = timezone.now()
    stats = {
        'total': base_stats_query.count(),
        'active': base_stats_query.filter(is_active=True).count(),
        'inactive': base_stats_query.filter(is_active=False).count(),
        'members': base_stats_query.filter(
            profile__is_member=True, 
            profile__member_until__gt=current_time
        ).count(),
        'expired_members': base_stats_query.filter(
            profile__is_member=True, 
            profile__member_until__lte=current_time
        ).count(),
    }
    
    # 构建自定义分页信息
    pagination = {
        'has_previous': page_number > 1,
        'has_next': page_number < total_pages,
        'current_page': page_number,
        'total_pages': total_pages,
        'page_range': range(max(1, page_number - 2), min(total_pages + 1, page_number + 3)),
        'previous_page_number': page_number - 1 if page_number > 1 else None,
        'next_page_number': page_number + 1 if page_number < total_pages else None,
        'items_count': total_count,
        'start_index': offset + 1 if total_count > 0 else 0,
        'end_index': min(offset + page_size, total_count),
    }
    
    # 记录日志
    admin_operate_log(request, "查看前台用户列表")
    
    # 获取会员类型选项
    MEMBER_TYPES = UserProfile._meta.get_field('member_type').choices
    
    context = {
        'user_list': user_list,
        'pagination': pagination,
        'total_users': stats['total'],
        'active_users': stats['active'],
        'inactive_users': stats['inactive'],
        'members': stats['members'],
        'expired_members': stats['expired_members'],
        'query': query,
        'is_active_filter': is_active_filter,
        'is_member_filter': is_member_filter,
        'member_type_filter': member_type_filter,
        'member_types': MEMBER_TYPES,
        'title': _('前台用户管理'),
        'now': timezone.now(),  # 添加当前时间用于模板中会员状态判断
        'site_title': _('GameHub管理系统'),
    }
    
    logger.info("成功加载前台用户列表页，显示第%s页，共%s条记录", page_number, len(user_list))
    return render(request, 'admin/front_user_list.html', context)

@login_required
@admin_login_required
def get_front_user_detail(request, user_id):
    """获取前台用户详情"""
    # 获取用户及其资料
    user = get_object_or_404(User, id=user_id, is_staff=False)
    
    # 获取或创建用户资料
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # 获取用户的游戏收藏数、游戏历史数和评论数
    favorite_count = user.profile.purchased_games.count() if hasattr(user, 'profile') else 0
    
    # 通过反向关系查询游戏历史和评论
    try:
        history_count = user.game_history.count() if hasattr(user, 'game_history') else 0
        comment_count = user.game_comments.count() if hasattr(user, 'game_comments') else 0
    except AttributeError:
        history_count = 0
        comment_count = 0
    
    # 会员状态
    is_active_member = profile.is_member and (not profile.member_until or profile.member_until > timezone.now())
    member_status = '活跃' if is_active_member else '非会员'
    if profile.is_member and profile.member_until and profile.member_until <= timezone.now():
        member_status = '已过期'
    
    # 获取会员类型显示值
    member_type_display = dict(UserProfile._meta.get_field('member_type').choices).get(profile.member_type, '未知')
    
    # 构建用户详情数据
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '从未登录',
        'is_active': user.is_active,
        'avatar_url': profile.avatar_url if hasattr(profile, 'avatar_url') and profile.avatar_url else (profile.avatar.url if profile.avatar else None),
        'is_member': profile.is_member,
        'member_type': member_type_display,
        'member_until': profile.member_until.strftime('%Y-%m-%d %H:%M:%S') if profile.member_until else '无期限',
        'member_status': member_status,
        'game_favorites': favorite_count,
        'game_history': history_count,
        'game_comments': comment_count,
        'bio': profile.bio,
        'role': profile.role if hasattr(profile, 'role') else '普通用户',
        'email_verified': hasattr(profile, 'email_verified') and profile.email_verified,
    }
    
    return JsonResponse({'success': True, 'user': user_data})

@login_required
@admin_login_required
@require_POST
def toggle_front_user_status(request, user_id):
    """切换前台用户状态（激活/禁用）"""
    user = get_object_or_404(User, id=user_id, is_staff=False)
    
    # 切换用户状态
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    
    # 记录操作日志
    status_text = '启用' if user.is_active else '禁用'
    admin_operate_log(request, f"{status_text}前台用户: {user.username}")
    
    messages.success(request, f"已{status_text}用户 {user.username}")
    return redirect('admin_panel:front_users_list')

@login_required
@admin_login_required
@require_POST
def reset_front_user_password(request, user_id):
    """重置前台用户密码"""
    user = get_object_or_404(User, id=user_id, is_staff=False)
    
    # 获取新密码
    new_password = request.POST.get('new_password')
    if not new_password:
        messages.error(request, "请提供新密码")
        return redirect('admin_panel:front_users_list')
    
    # 设置新密码
    user.set_password(new_password)
    user.save(update_fields=['password'])
    
    # 记录操作日志
    admin_operate_log(request, f"重置前台用户密码: {user.username}")
    
    messages.success(request, f"已重置用户 {user.username} 的密码")
    return redirect('admin_panel:front_users_list')

@login_required
@admin_login_required
@require_POST
def toggle_member_status(request, user_id):
    """切换前台用户会员状态"""
    user = get_object_or_404(User, id=user_id, is_staff=False)
    
    # 获取或创建用户资料
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # 切换会员状态
    profile.is_member = not profile.is_member
    
    # 如果设置为会员，默认给30天会员期
    if profile.is_member and not profile.member_until:
        profile.member_until = timezone.now() + timezone.timedelta(days=30)
        profile.member_type = 'monthly'
    
    profile.save(update_fields=['is_member', 'member_until', 'member_type'])
    
    # 记录操作日志
    status_text = '启用' if profile.is_member else '禁用'
    admin_operate_log(request, f"{status_text}前台用户会员状态: {user.username}")
    
    messages.success(request, f"已{status_text}用户 {user.username} 的会员状态")
    return redirect('admin_panel:front_users_list')

@login_required
@admin_login_required
@require_POST
def extend_member_until(request, user_id):
    """延长前台用户会员期限"""
    user = get_object_or_404(User, id=user_id, is_staff=False)
    
    # 获取或创建用户资料
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # 获取延长天数
    days = request.POST.get('days')
    try:
        days = int(days)
        if days <= 0:
            raise ValueError("天数必须为正整数")
    except (ValueError, TypeError):
        messages.error(request, "请提供有效的天数")
        return redirect('admin_panel:front_users_list')
    
    # 设置会员状态和期限
    profile.is_member = True
    
    # 如果当前没有会员期限或会员已过期，则从当前时间开始计算
    if not profile.member_until or profile.member_until < timezone.now():
        profile.member_until = timezone.now() + timezone.timedelta(days=days)
    else:
        # 否则在原有期限上延长
        profile.member_until = profile.member_until + timezone.timedelta(days=days)
    
    profile.save(update_fields=['is_member', 'member_until'])
    
    # 记录操作日志
    admin_operate_log(request, f"延长前台用户会员期限: {user.username}, 延长{days}天")
    
    messages.success(request, f"已延长用户 {user.username} 的会员期限 {days} 天")
    return redirect('admin_panel:front_users_list') 