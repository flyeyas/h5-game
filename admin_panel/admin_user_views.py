import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Case, When, IntegerField
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from admin_panel.forms import AdminUserForm
from admin_panel.models import AdminLog
from admin_panel.admin_user import AdminProfile
from core.api_utils import api_response

logger = logging.getLogger('admin')

# 自定义权限检查装饰器
def require_permissions(permission_list):
    """
    检查用户是否拥有指定权限的装饰器
    参数:
    - permission_list: 权限代码列表，例如 ['view_admin_users', 'add_admin_users']
    
    用法示例:
    @require_permissions(['view_admin_users'])
    def some_view(request):
        ...
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # 超级管理员拥有所有权限
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 检查是否是管理员
            if not is_admin(request.user):
                messages.error(request, _('您没有权限访问此页面'))
                return redirect('admin_panel:dashboard')
            
            # TODO: 实现更细粒度的权限检查逻辑
            # 这里简化处理，只要是管理员就拥有权限
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# 获取管理员用户列表的辅助函数
def get_admin_users():
    """获取所有管理员用户列表"""
    return get_user_model().objects.filter(is_staff=True).order_by('-date_joined')

# 管理员操作日志记录
def admin_operate_log(request, action_description):
    """记录管理员操作日志"""
    AdminLog.objects.create(
        admin=request.user,
        action=action_description,
        ip_address=request.META.get('REMOTE_ADDR', '')
    )

# 验证是否有管理员权限
def is_admin(user):
    return user.is_staff or user.is_superuser

# 管理员账号列表
@login_required
@user_passes_test(is_admin)
def list_admin_users(request):
    """管理员账号列表页面"""
    logger.info("访问管理员列表页面")
    
    # 获取查询参数
    query = request.GET.get('q', '')
    is_active_filter = request.GET.get('is_active', '')
    role_filter = request.GET.get('role', '')
    
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
    
    # 从AdminProfile表获取管理员列表，同时关联User表
    # 使用select_related提前加载关联的User对象，减少查询次数
    query_set = AdminProfile.objects.select_related('user').filter(user__is_staff=True)
    
    # 应用过滤条件
    if query:
        query_set = query_set.filter(
            Q(user__username__icontains=query) | 
            Q(user__email__icontains=query) |
            Q(real_name__icontains=query) |
            Q(mobile__icontains=query)
        )
    
    if is_active_filter != '':
        is_active = is_active_filter.lower() == 'true'
        query_set = query_set.filter(user__is_active=is_active)
    
    if role_filter:
        try:
            role_value = int(role_filter)
            query_set = query_set.filter(role=role_value)
        except (ValueError, TypeError):
            logger.warning("无效的角色过滤值: %s", role_filter)
    
    # 按用户创建时间降序排序
    query_set = query_set.order_by('-user__date_joined')
    
    # 获取总记录数，用于分页
    total_count = query_set.count()
    total_pages = (total_count + page_size - 1) // page_size  # 向上取整计算总页数
    
    # 使用 SQL LIMIT/OFFSET 进行数据库级分页
    admin_list = query_set[offset:offset + page_size]
    logger.info("执行数据库级分页查询: offset=%s, limit=%s", offset, page_size)
    
    # 创建基础查询用于统计，避免重复创建查询对象
    base_stats_query = AdminProfile.objects.filter(user__is_staff=True)
    
    # 使用聚合查询来减少数据库请求次数 - 统计活跃和非活跃用户
    stats = base_stats_query.aggregate(
        total=Count('id'),
        active=Count(Case(When(user__is_active=True, then=1), output_field=IntegerField())),
        super=Count(Case(When(user__is_superuser=True, then=1), output_field=IntegerField())),
        inactive=Count(Case(When(user__is_active=False, then=1), output_field=IntegerField()))
    )
    
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
    admin_operate_log(request, "查看管理员列表")
    
    context = {
        'admin_list': admin_list,
        'pagination': pagination,
        'total_admins': stats['total'],
        'active_admins': stats['active'],
        'super_admins': stats['super'],
        'inactive_admins': stats['inactive'],
        'query': query,
        'is_active_filter': is_active_filter,
        'role_filter': role_filter,
        'title': '管理员账号管理',
    }
    
    logger.info("成功加载管理员列表页，显示第%s页，共%s条记录", page_number, len(admin_list))
    return render(request, 'admin/admin_list.html', context)

# 添加管理员
@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_admin_user(request):
    """添加管理员页面"""
    logger.info("接收到创建管理员请求 - 请求方法: %s", request.method)
    
    if request.method == 'POST':
        # 记录提交的表单数据，用于调试
        logger.debug("POST数据内容:")
        for key, value in request.POST.items():
            logger.debug("- %s: %s", key, value)
        
        logger.debug("FILES数据内容:")
        for key, value in request.FILES.items():
            logger.debug("- %s: %s (类型: %s, 大小: %s字节)", 
                       key, value.name, value.content_type, value.size)
        
        # 特别检查关键字段
        real_name = request.POST.get('real_name', '')
        mobile = request.POST.get('mobile', '')
        notes = request.POST.get('notes', '')
        role_str = request.POST.get('role', '40')
        try:
            role = int(role_str)
        except (ValueError, TypeError):
            role = 40  # 默认值
        
        logger.info("关键字段检查:")
        logger.info("- real_name: '%s' (类型: %s, 空值: %s)", 
                   real_name, type(real_name).__name__, not bool(real_name))
        logger.info("- mobile: '%s' (类型: %s, 空值: %s)", 
                   mobile, type(mobile).__name__, not bool(mobile))
        logger.info("- notes: '%s' (类型: %s, 空值: %s)", 
                   notes, type(notes).__name__, not bool(notes))
        logger.info("- role: '%s' (类型: %s, 空值: %s)", 
                   role, type(role).__name__, not bool(role))
        logger.info("- avatar: %s", 'avatar' in request.FILES)
        logger.info("- random_avatar_url: '%s'", request.POST.get('random_avatar_url', ''))
        
        form = AdminUserForm(request.POST)
        if form.is_valid():
            logger.info("表单验证成功")
            admin_user = form.save(commit=False)
            
            # 确保是管理员
            admin_user.is_staff = True
            
            # 处理is_active状态
            is_active_val = request.POST.get('is_active', 'true')
            admin_user.is_active = is_active_val.lower() == 'true'
            logger.info("设置用户活动状态: %s", admin_user.is_active)
            
            # 设置密码
            if form.cleaned_data.get('password'):
                admin_user.set_password(form.cleaned_data['password'])
                logger.info("设置了用户密码")
            else:
                admin_user.set_unusable_password()
                logger.warning("没有设置密码，用户将无法登录")
            
            admin_user.save()
            logger.info("保存User模型成功，用户ID: %s", admin_user.id)
            
            # 设置扩展资料
            profile_data = {
                'real_name': real_name.strip(),
                'mobile': mobile.strip(),
                'notes': notes.strip(),
                'role': role,
                'status': 'active' if admin_user.is_active else 'inactive'
            }
            
            # 创建AdminProfile
            admin_profile = AdminProfile(user=admin_user)
            admin_profile.real_name = profile_data['real_name']
            admin_profile.mobile = profile_data['mobile']
            admin_profile.notes = profile_data['notes']
            admin_profile.role = profile_data['role']
            admin_profile.status = profile_data['status']
            
            # 处理头像
            avatar_handled = False
            # 只处理随机头像URL，不再上传头像文件
            if request.POST.get('random_avatar_url'):
                random_avatar_url = request.POST.get('random_avatar_url', '').strip()
                if random_avatar_url:
                    admin_profile.avatar_url = random_avatar_url
                    admin_profile.avatar = None
                    avatar_handled = True
                    logger.info("设置了随机头像URL: %s", random_avatar_url)
            else:
                # 如果没有设置随机头像，生成一个默认头像
                default_avatar_url = f"https://ui-avatars.com/api/?name={admin_user.username}&background=random&color=fff"
                admin_profile.avatar_url = default_avatar_url
                admin_profile.avatar = None
                avatar_handled = True
                logger.info("设置了默认头像URL: %s", default_avatar_url)
            
            # 保存资料
            try:
                admin_profile.save()
                logger.info("保存AdminProfile成功，ID: %s", admin_profile.id)
            except Exception as e:
                logger.error("保存AdminProfile时出错: %s", str(e), exc_info=True)
            
            # 检查保存后的结果
            try:
                # 强制从数据库重新获取，避免缓存问题
                saved_profile = AdminProfile.objects.get(user=admin_user)
                logger.debug("保存后的AdminProfile信息:")
                logger.debug("- ID: %s", saved_profile.id)
                logger.debug("- 用户: %s", saved_profile.user.username)
                logger.debug("- 姓名: '%s'", saved_profile.real_name)
                logger.debug("- 手机: '%s'", saved_profile.mobile)
                logger.debug("- 备注: '%s'", saved_profile.notes)
                logger.debug("- 角色: %s", saved_profile.role)
                logger.debug("- 状态: %s", saved_profile.status)
                logger.debug("- 头像: %s", saved_profile.avatar)
                logger.debug("- 头像URL: %s", saved_profile.avatar_url)
                
                # 检查字段是否成功保存
                if saved_profile.real_name != profile_data['real_name']:
                    logger.warning("姓名保存失败! 期望: '%s', 实际: '%s'", 
                                  profile_data['real_name'], saved_profile.real_name)
                if saved_profile.mobile != profile_data['mobile']:
                    logger.warning("手机保存失败! 期望: '%s', 实际: '%s'", 
                                  profile_data['mobile'], saved_profile.mobile)
                if saved_profile.notes != profile_data['notes']:
                    logger.warning("备注保存失败! 期望: '%s', 实际: '%s'", 
                                  profile_data['notes'], saved_profile.notes)
                if saved_profile.role != profile_data['role']:
                    logger.warning("角色保存失败! 期望: %s, 实际: %s", 
                                  profile_data['role'], saved_profile.role)
            except Exception as e:
                logger.error("获取保存后的AdminProfile失败: %s", str(e), exc_info=True)
            
            # 记录操作日志
            try:
                AdminLog.objects.create(
                    admin=request.user,
                    action=f'添加了管理员: {admin_user.username} (角色: {dict(AdminProfile.ROLES).get(profile_data["role"], "客服")})',
                    ip_address=request.META.get('REMOTE_ADDR', '')
                )
                logger.info("记录操作日志成功")
            except Exception as e:
                logger.error("记录操作日志失败: %s", str(e))
            
            # 对于AJAX请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                avatar_url = None
                if hasattr(admin_profile, 'avatar') and admin_profile.avatar and hasattr(admin_profile.avatar, 'url'):
                    avatar_url = admin_profile.avatar.url
                elif hasattr(admin_profile, 'avatar_url') and admin_profile.avatar_url:
                    avatar_url = admin_profile.avatar_url
                
                response_data = {
                    'status': 'success',
                    'message': _('管理员创建成功'),
                    'admin': {
                        'id': admin_user.id,
                        'username': admin_user.username,
                        'email': admin_user.email,
                        'is_active': admin_user.is_active,
                        'role': profile_data['role'],
                        'role_display': dict(AdminProfile.ROLES).get(profile_data['role'], '客服'),
                        'real_name': profile_data['real_name'], 
                        'mobile': profile_data['mobile'],
                        'avatar_url': avatar_url,
                        'notes': profile_data['notes']
                    }
                }
                logger.info("返回AJAX成功响应")
                logger.debug("响应数据: %s", response_data)
                return JsonResponse(response_data)
            
            messages.success(request, _('管理员创建成功'))
            logger.info("创建管理员完成，重定向到管理员列表页")
            return redirect('admin_panel:admin_users_list')
        else:
            # 记录表单验证错误
            logger.warning("表单验证错误: %s", form.errors)
            
            # 对于AJAX请求，返回验证错误信息
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                logger.info("返回AJAX错误响应")
                return JsonResponse({
                    'status': 'error',
                    'message': _('表单验证失败'),
                    'errors': {field: [str(error) for error in errors] for field, errors in form.errors.items()}
                })
    else:
        form = AdminUserForm()
        logger.info("GET请求，显示添加表单")
    
    return render(request, 'admin/admin_form.html', {
        'form': form,
        'title': _('添加管理员'),
        'is_add': True
    })

# 编辑管理员
@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_admin_user(request, admin_id):
    """编辑管理员页面"""
    logger.info("接收到编辑管理员请求 - admin_id: %s, 请求方法: %s, 路径: %s", 
               admin_id, request.method, request.path)
    
    admin_user = get_object_or_404(get_user_model(), id=admin_id, is_staff=True)
    logger.info("找到管理员用户: %s (ID: %s)", admin_user.username, admin_user.id)
    
    # 获取或创建用户资料
    try:
        admin_profile, created = AdminProfile.objects.get_or_create(user=admin_user)
        logger.info("%s AdminProfile对象成功", "创建" if created else "获取")
        logger.debug("编辑前的AdminProfile信息:")
        logger.debug("- ID: %s", admin_profile.id)
        logger.debug("- 用户: %s", admin_profile.user.username)
        logger.debug("- 姓名: '%s'", admin_profile.real_name)
        logger.debug("- 手机: '%s'", admin_profile.mobile)
        logger.debug("- 备注: '%s'", admin_profile.notes)
        logger.debug("- 角色: %s", admin_profile.role)
        logger.debug("- 状态: %s", admin_profile.status)
        logger.debug("- 头像: %s", admin_profile.avatar)
        logger.debug("- 头像URL: %s", admin_profile.avatar_url)
    except Exception as e:
        logger.error("获取AdminProfile失败: %s", str(e), exc_info=True)
        admin_profile = None
    
    if request.method == 'POST':
        # 记录请求头信息
        logger.debug("请求头信息:")
        for key, value in request.headers.items():
            logger.debug("- %s: %s", key, value)
        
        # 记录提交的表单数据，用于调试
        logger.debug("POST数据内容:")
        for key, value in request.POST.items():
            logger.debug("- %s: %s", key, value)
        
        logger.debug("FILES数据内容:")
        for key, value in request.FILES.items():
            logger.debug("- %s: %s (类型: %s, 大小: %s字节)", 
                       key, value.name, value.content_type, value.size)
            
        # 特别检查关键字段
        real_name = request.POST.get('real_name', '')
        mobile = request.POST.get('mobile', '')
        notes = request.POST.get('notes', '')
        role_str = request.POST.get('role', '40')
        try:
            role = int(role_str)
        except (ValueError, TypeError):
            role = 40  # 默认值
        
        logger.info("关键字段检查:")
        logger.info("- real_name: '%s' (类型: %s, 空值: %s)", 
                   real_name, type(real_name).__name__, not bool(real_name))
        logger.info("- mobile: '%s' (类型: %s, 空值: %s)", 
                   mobile, type(mobile).__name__, not bool(mobile))
        logger.info("- notes: '%s' (类型: %s, 空值: %s)", 
                   notes, type(notes).__name__, not bool(notes))
        logger.info("- role: '%s' (类型: %s, 空值: %s)", 
                   role, type(role).__name__, not bool(role))
        logger.info("- avatar: %s", 'avatar' in request.FILES)
        logger.info("- random_avatar_url: '%s'", request.POST.get('random_avatar_url', ''))
        
        form = AdminUserForm(request.POST, instance=admin_user)
        if form.is_valid():
            logger.info("表单验证成功")
            # 如果提供了新密码，则更新密码
            if form.cleaned_data.get('password'):
                admin_user.password = make_password(form.cleaned_data['password'])
                logger.info("更新了用户密码")
            
            admin_user = form.save(commit=False)
            # 确保是管理员
            admin_user.is_staff = True
            
            # 处理is_active状态
            is_active_val = request.POST.get('is_active', 'true')
            admin_user.is_active = is_active_val.lower() == 'true'
            logger.info("设置用户活动状态: %s", admin_user.is_active)
            
            admin_user.save()
            logger.info("保存User模型成功")
            
            # 处理AdminProfile - 使用直接的数据库更新方式
            profile_data = {
                'real_name': real_name.strip(),
                'mobile': mobile.strip(),
                'notes': notes.strip(),
                'role': role,
                'status': 'active' if admin_user.is_active else 'inactive'
            }
            
            # 处理头像
            avatar_updated = False
            # 只处理随机头像URL，不再上传头像文件
            if request.POST.get('random_avatar_url'):
                random_avatar_url = request.POST.get('random_avatar_url', '').strip()
                if random_avatar_url and admin_profile:
                    # 设置随机头像URL
                    admin_profile.avatar_url = random_avatar_url
                    admin_profile.avatar = None
                    avatar_updated = True
                    logger.info("设置了新的随机头像URL: %s", random_avatar_url)
                    try:
                        admin_profile.save(update_fields=['avatar', 'avatar_url'])
                        logger.info("头像URL更新成功")
                    except Exception as e:
                        logger.error("更新头像URL字段时出错: %s", str(e), exc_info=True)
            
            # 使用更新方式保存Profile字段（不包括头像字段，已单独处理）
            try:
                update_result = AdminProfile.objects.filter(user=admin_user).update(
                    real_name=profile_data['real_name'],
                    mobile=profile_data['mobile'],
                    notes=profile_data['notes'],
                    role=profile_data['role'],
                    status=profile_data['status']
                )
                logger.info("使用update方法更新AdminProfile成功, 影响行数: %s", update_result)
                
                # 如果update没有成功（返回0），尝试重新创建
                if update_result == 0:
                    logger.warning("update方法没有更新任何记录，尝试重新创建")
                    if not admin_profile:
                        admin_profile = AdminProfile(user=admin_user)
                        logger.info("重新创建AdminProfile对象")
                    
                    admin_profile.real_name = profile_data['real_name']
                    admin_profile.mobile = profile_data['mobile']
                    admin_profile.notes = profile_data['notes']
                    admin_profile.role = profile_data['role']
                    admin_profile.status = profile_data['status']
                    
                    # 如果头像还没处理过，在这里一起处理
                    if not avatar_updated:
                        if request.POST.get('random_avatar_url'):
                            random_avatar_url = request.POST.get('random_avatar_url', '').strip()
                            if random_avatar_url:
                                admin_profile.avatar_url = random_avatar_url
                                admin_profile.avatar = None
                                logger.info("在备用方法中设置随机头像URL")
                        else:
                            # 如果没有设置随机头像，生成一个默认头像
                            default_avatar_url = f"https://ui-avatars.com/api/?name={admin_user.username}&background=random&color=fff"
                            admin_profile.avatar_url = default_avatar_url
                            admin_profile.avatar = None
                            logger.info("在备用方法中设置默认头像URL: %s", default_avatar_url)
                    
                    admin_profile.save()
                    logger.info("使用save方法保存AdminProfile成功")
            except Exception as e:
                logger.error("使用update方法更新AdminProfile失败: %s", str(e), exc_info=True)
                
                # 尝试备用方法 - 使用原始的save方法
                try:
                    if admin_profile:
                        admin_profile.real_name = profile_data['real_name']
                        admin_profile.mobile = profile_data['mobile']
                        admin_profile.notes = profile_data['notes']
                        admin_profile.role = profile_data['role']
                        admin_profile.status = profile_data['status']
                        
                        # 如果头像还没处理过，在这里一起处理
                        if not avatar_updated:
                            if request.POST.get('random_avatar_url'):
                                random_avatar_url = request.POST.get('random_avatar_url', '').strip()
                                if random_avatar_url:
                                    admin_profile.avatar_url = random_avatar_url
                                    admin_profile.avatar = None
                                    logger.info("在备用方法中设置随机头像URL")
                            else:
                                # 如果没有设置随机头像，生成一个默认头像
                                default_avatar_url = f"https://ui-avatars.com/api/?name={admin_user.username}&background=random&color=fff"
                                admin_profile.avatar_url = default_avatar_url
                                admin_profile.avatar = None
                                logger.info("在备用方法中设置默认头像URL: %s", default_avatar_url)
                        
                        admin_profile.save()
                        logger.info("使用备用方法保存AdminProfile成功")
                except Exception as e2:
                    logger.error("备用方法保存AdminProfile也失败: %s", str(e2), exc_info=True)
                    
                    # 最终尝试 - 删除原有配置文件并创建新的
                    try:
                        if admin_profile and admin_profile.id:
                            admin_profile.delete()
                            logger.info("删除原有AdminProfile记录")
                        
                        admin_profile = AdminProfile(
                            user=admin_user,
                            real_name=profile_data['real_name'],
                            mobile=profile_data['mobile'],
                            notes=profile_data['notes'],
                            role=profile_data['role'],
                            status=profile_data['status']
                        )
                        
                        # 处理头像
                        if 'avatar' in request.FILES and request.FILES['avatar']:
                            admin_profile.avatar = request.FILES['avatar']
                            logger.info("在最终尝试中设置头像文件")
                        elif request.POST.get('random_avatar_url'):
                            random_avatar_url = request.POST.get('random_avatar_url', '').strip()
                            if random_avatar_url:
                                admin_profile.avatar_url = random_avatar_url
                                logger.info("在最终尝试中设置随机头像URL")
                        
                        admin_profile.save()
                        logger.info("使用最终尝试方法创建新的AdminProfile成功")
                    except Exception as e3:
                        logger.error("最终尝试保存AdminProfile也失败: %s", str(e3), exc_info=True)
            
            # 检查保存后的结果
            try:
                # 强制从数据库重新获取，避免缓存问题
                saved_profile = AdminProfile.objects.get(user=admin_user)
                logger.debug("保存后的AdminProfile信息:")
                logger.debug("- ID: %s", saved_profile.id)
                logger.debug("- 用户: %s", saved_profile.user.username)
                logger.debug("- 姓名: '%s'", saved_profile.real_name)
                logger.debug("- 手机: '%s'", saved_profile.mobile)
                logger.debug("- 备注: '%s'", saved_profile.notes)
                logger.debug("- 角色: %s", saved_profile.role)
                logger.debug("- 状态: %s", saved_profile.status)
                logger.debug("- 头像: %s", saved_profile.avatar)
                logger.debug("- 头像URL: %s", saved_profile.avatar_url)
                
                # 检查字段是否成功保存
                if saved_profile.real_name != profile_data['real_name']:
                    logger.warning("姓名保存失败! 期望: '%s', 实际: '%s'", 
                                  profile_data['real_name'], saved_profile.real_name)
                if saved_profile.mobile != profile_data['mobile']:
                    logger.warning("手机保存失败! 期望: '%s', 实际: '%s'", 
                                  profile_data['mobile'], saved_profile.mobile)
                if saved_profile.notes != profile_data['notes']:
                    logger.warning("备注保存失败! 期望: '%s', 实际: '%s'", 
                                  profile_data['notes'], saved_profile.notes)
                if saved_profile.role != profile_data['role']:
                    logger.warning("角色保存失败! 期望: %s, 实际: %s", 
                                  profile_data['role'], saved_profile.role)
            except Exception as e:
                logger.error("获取保存后的AdminProfile失败: %s", str(e), exc_info=True)
            
            # 记录操作日志
            try:
                AdminLog.objects.create(
                    admin=request.user,
                    action=f'编辑了管理员: {admin_user.username} (角色: {profile_data["role"]})',
                    ip_address=request.META.get('REMOTE_ADDR', '')
                )
                logger.info("记录操作日志成功")
            except Exception as e:
                logger.error("记录操作日志失败: %s", str(e))
            
            # 对于AJAX请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                avatar_url = None
                if admin_profile:
                    if admin_profile.avatar and hasattr(admin_profile.avatar, 'url'):
                        avatar_url = admin_profile.avatar.url
                    elif admin_profile.avatar_url:
                        avatar_url = admin_profile.avatar_url
                
                response_data = {
                    'status': 'success',
                    'message': _('管理员信息更新成功'),
                    'admin': {
                        'id': admin_user.id,
                        'username': admin_user.username,
                        'first_name': admin_user.first_name,
                        'last_name': admin_user.last_name,
                        'email': admin_user.email,
                        'is_active': admin_user.is_active,
                        'role': profile_data['role'],
                        'role_display': dict(AdminProfile.ROLES).get(profile_data['role'], '客服'),
                        'real_name': profile_data['real_name'],
                        'mobile': profile_data['mobile'],
                        'avatar_url': avatar_url,
                        'notes': profile_data['notes']
                    }
                }
                logger.info("返回AJAX成功响应")
                logger.debug("响应数据: %s", response_data)
                return JsonResponse(response_data)
            
            messages.success(request, _('管理员信息更新成功'))
            logger.info("编辑管理员完成，重定向到管理员列表页")
            return redirect('admin_panel:admin_users_list')
        else:
            # 记录表单验证错误
            logger.warning("表单验证错误: %s", form.errors)
            
            # 对于AJAX请求，返回验证错误信息
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                logger.info("返回AJAX错误响应")
                return JsonResponse({
                    'status': 'error',
                    'message': _('表单验证失败'),
                    'errors': {field: [str(error) for error in errors] for field, errors in form.errors.items()}
                })
    else:
        form = AdminUserForm(instance=admin_user)
        logger.info("GET请求，显示编辑表单")
    
    return render(request, 'admin/admin_form.html', {
        'form': form,
        'admin_user': admin_user,
        'admin_profile': admin_profile,  # 传递AdminProfile到模板
        'title': _('编辑管理员'),
        'is_add': False
    })

# 删除管理员
@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def remove_admin_user(request, admin_id):
    """删除管理员"""
    admin_user = get_object_or_404(get_user_model(), id=admin_id, is_staff=True)
    
    # 不能删除自己
    if admin_user.id == request.user.id:
        return api_response(
            success=False,
            message=_('不能删除自己的账号'),
            code='forbidden'
        )
    
    try:
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=f'删除了管理员: {admin_user.username}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # 删除账号
        admin_user.delete()
        
        # 返回成功响应
        return api_response(
            success=True,
            message=_('管理员账号已删除'),
            code='success',
            data={'admin_id': admin_id}
        )
    except Exception as e:
        logger.error(f"删除管理员失败: {str(e)}")
        return api_response(
            success=False,
            message=_('删除管理员失败: ') + str(e),
            code='internal_error',
            errors={'detail': str(e)}
        )

# 启用/禁用管理员账号
@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def switch_admin_status(request, admin_id):
    """启用/禁用管理员账号"""
    admin_user = get_object_or_404(get_user_model(), id=admin_id, is_staff=True)
    
    # 不能修改自己的状态
    if admin_user.id == request.user.id:
        messages.error(request, _('不能修改自己的账号状态'))
        return redirect('admin_panel:admin_users_list')
    
    # 切换状态
    admin_user.is_active = not admin_user.is_active
    admin_user.save()
    
    # 记录操作日志
    status_str = '启用' if admin_user.is_active else '禁用'
    AdminLog.objects.create(
        admin=request.user,
        action=f'{status_str}了管理员账号: {admin_user.username}',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    messages.success(request, _(f'管理员账号已{status_str}'))
    return redirect('admin_panel:admin_users_list')

@login_required
@user_passes_test(is_admin)
def admin_users_list(request):
    """
    管理员用户列表页
    该函数已被list_admin_users替代，保留此函数以确保向后兼容性
    """
    # 重定向到新的list_admin_users视图
    return list_admin_users(request)

@login_required
@user_passes_test(is_admin)
def get_admin_detail(request, admin_id):
    """
    获取单个管理员的详细信息API
    返回JSON格式的管理员信息
    """
    logger.info("获取管理员详细信息API请求 - admin_id: %s", admin_id)
    
    try:
        # 获取用户基本信息
        user = get_object_or_404(get_user_model(), id=admin_id)
        logger.info("找到管理员用户: %s (ID: %s)", user.username, user.id)
        
        # 获取用户扩展资料
        try:
            admin_profile = AdminProfile.objects.get(user=user)
            logger.info("找到管理员资料 (ID: %s)", admin_profile.id)
            
            # 处理头像URL
            avatar_url = ""
            if admin_profile.avatar and hasattr(admin_profile.avatar, 'url'):
                avatar_url = admin_profile.avatar.url
                logger.info("使用上传的头像: %s", avatar_url)
            elif admin_profile.avatar_url:
                avatar_url = admin_profile.avatar_url
                logger.info("使用头像URL: %s", avatar_url)
            else:
                # 生成默认头像URL
                avatar_url = f"https://ui-avatars.com/api/?name={user.username}&background=random&color=fff"
                logger.info("生成默认头像URL: %s", avatar_url)
            
            # 角色显示名称
            role_display = dict(AdminProfile.ROLES).get(admin_profile.role, '未知角色')
            
            # 构建管理员资料JSON对象
            admin_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                'real_name': admin_profile.real_name,
                'mobile': admin_profile.mobile,
                'notes': admin_profile.notes,
                'role': admin_profile.role,
                'role_display': role_display,
                'avatar_url': avatar_url,
                'status': 'active' if user.is_active else 'inactive'
            }
            
        except AdminProfile.DoesNotExist:
            logger.warning("管理员资料不存在，创建默认资料")
            # 用户存在但没有扩展资料，创建一个默认的资料
            admin_profile = AdminProfile(
                user=user,
                real_name="",
                mobile="",
                notes="",
                role=40,  # 默认角色为Agent
                status='active' if user.is_active else 'inactive'
            )
            admin_profile.save()
            logger.info("创建了默认的管理员资料 ID: %s", admin_profile.id)
            
            # 生成默认头像URL
            avatar_url = f"https://ui-avatars.com/api/?name={user.username}&background=random&color=fff"
            
            # 构建基本的管理员数据
            admin_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                'real_name': '',
                'mobile': '',
                'notes': '',
                'role': 40,  # 默认角色为Agent
                'role_display': 'Agent',
                'avatar_url': avatar_url,
                'status': 'active' if user.is_active else 'inactive'
            }
        
        logger.info("成功生成管理员数据JSON")
        return JsonResponse({
            'status': 'success',
            'admin': admin_data
        })
        
    except Exception as e:
        logger.error("获取管理员详情失败: %s", str(e), exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'获取管理员详情失败: {str(e)}'
        }, status=500)