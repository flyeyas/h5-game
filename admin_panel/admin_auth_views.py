from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import json
import logging
from core.api_utils import api_response

logger = logging.getLogger('admin')

@ensure_csrf_cookie
def login_view(request):
    """管理员登录页面"""
    if request.user.is_authenticated and request.user.is_staff:
        # 已登录的管理员用户重定向到后台首页
        return redirect('admin_panel:dashboard')
    
    # 处理常规表单登录提交
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me', False)
        
        if username and password:
            user = authenticate(username=username, password=password)
            
            if user is not None and user.is_active and user.is_staff:
                login(request, user)
                
                # 设置会话过期时间
                if not remember_me:
                    request.session.set_expiry(0)
                
                logger.info(f"管理员 {username} 通过表单提交登录成功")
                
                # 获取重定向URL
                next_url = request.POST.get('next', reverse('admin_panel:dashboard'))
                return redirect(next_url)
            else:
                if user is None:
                    messages.error(request, _('用户名或密码错误'))
                elif not user.is_active:
                    messages.error(request, _('账户已被禁用'))
                elif not user.is_staff:
                    messages.error(request, _('您没有管理员权限'))
                logger.warning(f"用户 {username} 通过表单提交登录失败")
        else:
            messages.error(request, _('请输入用户名和密码'))
    
    context = {
        'site_title': _('游戏中心管理系统'),
        'site_header': _('管理员登录')
    }
    
    return render(request, 'admin/login.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def ajax_login_view(request):
    """处理AJAX登录请求
    
    接收JSON格式的登录请求，返回统一格式的JSON响应
    
    请求格式:
    {
        "username": "用户名",
        "password": "密码",
        "remember_me": true/false (可选)
    }
    """
    logger.info("接收到ajax登录请求")
    
    # 解析JSON请求体，不检查Content-Type
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('remember_me', False)
        logger.debug(f"JSON请求数据: username={username}, remember_me={remember_me}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return api_response(
            success=False,
            message=_('无效的JSON格式'),
            code='bad_request'
        )
    
    # 验证用户名和密码
    if not username or not password:
        logger.warning("用户名或密码为空")
        return api_response(
            success=False,
            message=_('用户名和密码不能为空'),
            code='validation_error',
            errors={
                'username': None if username else _('用户名不能为空'),
                'password': None if password else _('密码不能为空')
            }
        )
    
    # 尝试登录
    user = authenticate(username=username, password=password)
    
    if user is None:
        # 记录登录失败
        logger.warning(f"用户 {username} 登录失败，密码错误")
        return api_response(
            success=False,
            message=_('用户名或密码错误'),
            code='unauthorized'
        )
    
    if not user.is_active:
        logger.warning(f"禁用用户 {username} 尝试登录")
        return api_response(
            success=False,
            message=_('账户已被禁用，请联系管理员'),
            code='forbidden'
        )
    
    if not user.is_staff:
        logger.warning(f"非管理员用户 {username} 尝试登录管理后台")
        return api_response(
            success=False,
            message=_('您没有管理员权限'),
            code='forbidden'
        )
    
    # 登录成功
    login(request, user)
    
    # 设置会话过期时间
    if not remember_me:
        # 浏览器关闭后会话过期
        request.session.set_expiry(0)
    
    logger.info(f"管理员 {username} 登录成功")
    
    # 返回成功消息和用户信息
    return api_response(
        success=True,
        message=_('登录成功'),
        code='success',
        data={
            'username': user.username,
            'redirect_url': reverse('admin_panel:dashboard'),
            'user_id': user.id,
            'is_superuser': user.is_superuser,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    ) 