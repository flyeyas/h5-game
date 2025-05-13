from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.cache import cache
from django.core.mail import send_mail, EmailMessage
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse
import json
import smtplib
import ssl
import io
import logging
import traceback
import socket
from datetime import datetime
import subprocess
import platform
import re

from .email_settings import EmailSettings
from .email_settings_forms import EmailSettingsForm
from .admin_site import custom_staff_member_required
from .models import AdminLog

# 获取日志记录器
logger = logging.getLogger(__name__)

# 创建一个特殊的日志处理器，捕获SMTP通信日志
class SMTPDebugOutput(io.StringIO):
    def __init__(self):
        super().__init__()
        self.log = []
    
    def write(self, s):
        self.log.append(s)
        return super().write(s)
    
    def get_log(self):
        return "".join(self.log)

@custom_staff_member_required
@permission_required('admin_panel.setting_view', raise_exception=True)
@ensure_csrf_cookie
def email_settings_view(request):
    """邮件设置查看页面"""
    # 获取或创建邮件设置
    email_settings = EmailSettings.get_settings()
    
    # 处理非Ajax表单提交 (传统方式，保留向后兼容性)
    if request.method == 'POST' and request.user.has_perm('admin_panel.setting_edit') and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = EmailSettingsForm(request.POST)
        if form.is_valid():
            # 更新设置
            for field_name, field_value in form.cleaned_data.items():
                if field_name != 'test_email' and hasattr(email_settings, field_name):
                    setattr(email_settings, field_name, field_value)
            
            # 保存设置
            email_settings.save()
            
            # 记录操作日志
            AdminLog.objects.create(
                admin=request.user,
                action=_('更新了邮件设置'),
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, _('邮件设置已成功更新'))
            return redirect('admin_panel:email_settings')
    else:
        # 初始化表单数据
        initial_data = {
            'enable_smtp': email_settings.enable_smtp,
            'smtp_server': email_settings.smtp_server,
            'smtp_port': email_settings.smtp_port,
            'security_type': email_settings.security_type,
            'require_authentication': email_settings.require_authentication,
            'smtp_username': email_settings.smtp_username,
            'smtp_password': email_settings.smtp_password,
            'sender_email': email_settings.sender_email,
            'sender_name': email_settings.sender_name,
            'send_timeout': email_settings.send_timeout
        }
        form = EmailSettingsForm(initial=initial_data)
    
    context = {
        'title': _('邮件配置'),
        'form': form,
        'email_settings': email_settings
    }
    
    return render(request, 'admin/email_settings.html', context)

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
@require_http_methods(["POST"])
def ajax_update_email_settings(request):
    """通过Ajax更新邮件设置"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': _('非法请求')}, status=400)
    
    # 获取现有设置
    email_settings = EmailSettings.get_settings()
    
    # 使用表单验证数据
    form = EmailSettingsForm(request.POST)
    
    if form.is_valid():
        # 更新设置
        for field_name, field_value in form.cleaned_data.items():
            if field_name != 'test_email' and hasattr(email_settings, field_name):
                setattr(email_settings, field_name, field_value)
        
        # 保存设置
        email_settings.save()
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=_('通过Ajax更新了邮件设置'),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': _('邮件设置已成功更新')
        })
    else:
        # 返回表单错误
        errors = {}
        for field in form.errors:
            errors[field] = form.errors[field][0]
        
        return JsonResponse({
            'success': False,
            'error': _('表单验证失败'),
            'errors': errors
        }, status=400)

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
@require_http_methods(["POST"])
def clear_email_settings_cache(request):
    """清除邮件设置缓存"""
    EmailSettings.clear_cache()
    return JsonResponse({'success': True, 'message': _('邮件设置缓存已清除')})

@custom_staff_member_required
@permission_required('admin_panel.setting_edit', raise_exception=True)
@require_http_methods(["POST"])
def test_email(request):
    """发送测试邮件"""
    try:
        data = json.loads(request.body)
        test_email = data.get('test_email')
        
        if not test_email:
            return JsonResponse({'success': False, 'error': _('请提供测试邮箱地址')}, status=400)
        
        # 从请求中获取临时邮件设置
        temp_settings = {
            'enable_smtp': data.get('enable_smtp', True),  # 默认启用SMTP
            'smtp_server': data.get('smtp_server', ''),
            'smtp_port': int(data.get('smtp_port', 25)),
            'security_type': data.get('security_type', 'none'),
            'require_authentication': data.get('require_authentication', False),
            'smtp_username': data.get('smtp_username', ''),
            'smtp_password': data.get('smtp_password', ''),
            'sender_email': data.get('sender_email', ''),
            'sender_name': data.get('sender_name', '')
        }
        
        # 验证设置
        if not temp_settings['smtp_server']:
            return JsonResponse({'success': False, 'error': _('SMTP服务器地址不能为空')}, status=400)
        
        if not temp_settings['smtp_port']:
            return JsonResponse({'success': False, 'error': _('SMTP端口不能为空')}, status=400)
        
        if not temp_settings['sender_email']:
            return JsonResponse({'success': False, 'error': _('发送邮箱不能为空')}, status=400)
        
        if temp_settings['require_authentication']:
            if not temp_settings['smtp_username']:
                return JsonResponse({'success': False, 'error': _('SMTP用户名不能为空')}, status=400)
            
            if not temp_settings['smtp_password']:
                return JsonResponse({'success': False, 'error': _('SMTP密码不能为空')}, status=400)
        
        # 发送测试邮件
        from_email = f"{temp_settings['sender_name']} <{temp_settings['sender_email']}>" if temp_settings['sender_name'] else temp_settings['sender_email']
        
        # 准备调试输出
        debug_output = SMTPDebugOutput()
        smtp_debug_log = []
        
        # 网络连接诊断
        smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] === 开始网络连接诊断 ===")
        
        # 获取操作系统信息
        os_info = platform.platform()
        smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 操作系统: {os_info}")
        
        # 尝试解析服务器IP
        try:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 尝试解析SMTP服务器IP: {temp_settings['smtp_server']}")
            server_ip = socket.gethostbyname(temp_settings['smtp_server'])
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 服务器IP: {server_ip}")
        except Exception as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] DNS解析失败: {str(e)}")
            server_ip = None
        
        # 尝试TCP连接测试
        try:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 测试TCP连接到 {temp_settings['smtp_server']}:{temp_settings['smtp_port']}")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            start_time = datetime.now()
            s.connect((temp_settings['smtp_server'], temp_settings['smtp_port']))
            end_time = datetime.now()
            connection_time = (end_time - start_time).total_seconds()
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] TCP连接成功，延迟: {connection_time:.2f}秒")
            s.close()
        except Exception as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] TCP连接失败: {str(e)}")
        
        # 尝试ping测试
        try:
            if server_ip:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 尝试Ping测试 {server_ip}")
                
                # 根据操作系统确定正确的ping命令
                if platform.system().lower() == "windows":
                    ping_cmd = ["ping", "-n", "3", server_ip]
                else:
                    ping_cmd = ["ping", "-c", "3", server_ip]
                
                ping_result = subprocess.run(ping_cmd, capture_output=True, text=True)
                
                if ping_result.returncode == 0:
                    # 提取ping结果中的平均延迟
                    output = ping_result.stdout
                    if platform.system().lower() == "windows":
                        match = re.search(r"Average = (\d+)ms", output)
                    else:
                        match = re.search(r"min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms", output)
                    
                    avg_time = match.group(1) if match else "未知"
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Ping成功，平均延迟: {avg_time}ms")
                else:
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Ping失败: {ping_result.stderr}")
            else:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 跳过Ping测试: 无法解析服务器IP")
        except Exception as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Ping测试异常: {str(e)}")
        
        smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] === 网络诊断完成 ===")
        
        # 使用SMTP直接发送测试邮件
        try:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 开始连接SMTP服务器: {temp_settings['smtp_server']}:{temp_settings['smtp_port']}")
            
            # 设置调试级别
            old_debuglevel = smtplib.SMTP.debuglevel
            smtplib.SMTP.debuglevel = 1
            
            # 创建SMTP连接
            if temp_settings['security_type'] == 'ssl':
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 使用SSL加密连接")
                context = ssl.create_default_context()
                # 添加SSL兼容性设置
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] SSL设置: 禁用主机名检查和证书验证以增加兼容性")
                
                try:
                    server = smtplib.SMTP_SSL(
                        temp_settings['smtp_server'], 
                        temp_settings['smtp_port'], 
                        context=context, 
                        timeout=30
                    )
                    server.set_debuglevel(1)
                except Exception as e:
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 使用SSL连接失败: {str(e)}")
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 尝试不使用SSL context连接...")
                    server = smtplib.SMTP_SSL(
                        temp_settings['smtp_server'], 
                        temp_settings['smtp_port'], 
                        timeout=30
                    )
                    server.set_debuglevel(1)
            else:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 使用普通连接")
                server = smtplib.SMTP(
                    temp_settings['smtp_server'], 
                    temp_settings['smtp_port'], 
                    timeout=30
                )
                server.set_debuglevel(1)
            
            # 测试连接
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 测试服务器连接...")
            server_info = server.ehlo()
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 服务器响应: {server_info}")
            
            # TLS加密
            if temp_settings['security_type'] == 'tls':
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 启动TLS加密")
                try:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    server.starttls(context=context)
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] TLS连接成功")
                except Exception as e:
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] TLS连接失败: {str(e)}")
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 尝试不使用SSL context的TLS连接...")
                    server.starttls()
            
            # 获取支持的认证方式
            try:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 检查服务器支持的认证方式...")
                auth_methods = server.esmtp_features.get('auth', '').strip().upper()
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 服务器支持的认证方式: {auth_methods}")
            except:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 无法获取服务器支持的认证方式")
            
            # 认证
            if temp_settings['require_authentication']:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 尝试SMTP认证: 用户名={temp_settings['smtp_username']}")
                try:
                    server.login(temp_settings['smtp_username'], temp_settings['smtp_password'])
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 认证成功")
                except smtplib.SMTPAuthenticationError as e:
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 标准认证失败: {str(e)}")
                    smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 尝试替代认证方法...")
                    
                    try:
                        # 尝试使用AUTH LOGIN方法
                        import base64
                        smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 尝试AUTH LOGIN认证方法")
                        server.ehlo()
                        server.docmd("AUTH LOGIN")
                        server.docmd(base64.b64encode(temp_settings['smtp_username'].encode()).decode())
                        server.docmd(base64.b64encode(temp_settings['smtp_password'].encode()).decode())
                        smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] AUTH LOGIN认证成功")
                    except Exception as auth_error:
                        smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] AUTH LOGIN认证失败: {str(auth_error)}")
                        # 继续抛出原始异常
                        raise e
                    
            # 设置邮件发送额外选项
            try:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 设置SMTP额外选项...")
                server.ehlo_or_helo_if_needed()
                
                # 获取服务器的本地主机名
                local_hostname = server.local_hostname
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 本地主机名: {local_hostname}")
            except Exception as e:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 设置额外选项时出错: {str(e)}")
            
            # 创建邮件消息
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 准备发送邮件: 从 {from_email} 到 {test_email}")
            
            # 强制将延迟翻译对象转换为字符串
            subject_str = str(_('GameHub邮件系统测试'))
            message_str = str(_('这是一封测试邮件，如果您收到此邮件，说明您的邮件系统配置正确。'))
            team_str = str(_('GameHub团队'))
            auto_mail_str = str(_('此邮件由系统自动发送，请勿回复。'))
            
            html_message = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 5px;">
                <h2 style="color: #333;">{subject_str}</h2>
                <p style="color: #666; line-height: 1.6;">{message_str}</p>
                <p style="color: #666; line-height: 1.6;">{auto_mail_str}</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">&copy; {team_str}</p>
            </div>
            """
            
            # 使用Python标准库创建邮件
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject_str
            msg['From'] = from_email
            msg['To'] = test_email
            
            text_part = MIMEText(message_str, 'plain', 'utf-8')
            html_part = MIMEText(html_message, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # 发送邮件
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 发送邮件...")
            
            try:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 使用server.sendmail()方法发送")
                server.sendmail(from_email, [test_email], msg.as_string())
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 邮件发送成功")
            except Exception as e:
                smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 发送失败: {str(e)}")
                raise
            
            server.quit()
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] SMTP连接已关闭")
            
            # 重置调试级别
            smtplib.SMTP.debuglevel = old_debuglevel
            
            # 记录操作日志
            AdminLog.objects.create(
                admin=request.user,
                action=_('发送了测试邮件到 %s') % test_email,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True, 
                'message': _('测试邮件已发送'),
                'debug_log': smtp_debug_log
            })
        
        except ConnectionRefusedError as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: 连接被拒绝 - {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': _('连接被拒绝: 无法连接到SMTP服务器。请检查服务器地址和端口是否正确。'),
                'error_detail': str(e),
                'debug_log': smtp_debug_log
            }, status=500)
        except smtplib.SMTPAuthenticationError as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: 认证失败 - {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': _('SMTP认证失败: 用户名或密码不正确。'),
                'error_detail': str(e),
                'debug_log': smtp_debug_log
            }, status=500)
        except smtplib.SMTPException as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: SMTP错误 - {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': _('SMTP错误: %s') % str(e),
                'error_detail': str(e),
                'debug_log': smtp_debug_log
            }, status=500)
        except ssl.SSLError as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: SSL错误 - {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': _('SSL/TLS错误: 安全连接失败。请检查是否选择了正确的安全连接类型。'),
                'error_detail': str(e),
                'debug_log': smtp_debug_log
            }, status=500)
        except TimeoutError as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: 连接超时 - {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': _('连接超时: 服务器响应时间过长或无法访问。'),
                'error_detail': str(e),
                'debug_log': smtp_debug_log
            }, status=500)
        except OSError as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: 网络错误 - {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': _('网络错误: %s') % str(e),
                'error_detail': str(e),
                'debug_log': smtp_debug_log
            }, status=500)
        except Exception as e:
            smtp_debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: 未知错误 - {str(e)}")
            smtp_debug_log.append(traceback.format_exc())
            return JsonResponse({
                'success': False, 
                'error': _('发送邮件时出现未知错误'),
                'error_detail': str(e),
                'debug_log': smtp_debug_log
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('无效的请求数据')}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500) 