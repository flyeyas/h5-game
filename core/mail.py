import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail import send_mail as django_send_mail, EmailMultiAlternatives
from django.conf import settings
import logging

from .email_config import EmailConfig

logger = logging.getLogger(__name__)

def send_mail(subject, message, recipient_list, from_email=None, html_message=None, fail_silently=False):
    """
    发送电子邮件的函数，使用数据库中存储的SMTP配置。
    这个函数是对Django send_mail的包装，可以动态应用数据库中的配置。
    
    参数:
        subject (str): 邮件主题
        message (str): 邮件纯文本内容
        recipient_list (list): 收件人邮箱列表
        from_email (str, optional): 发件人邮箱。如果为None，将使用配置中的默认值
        html_message (str, optional): 邮件HTML内容
        fail_silently (bool, optional): 是否静默失败。默认为False
        
    返回:
        bool: 发送成功返回True，失败返回False
    """
    try:
        # 获取邮件配置
        email_config = EmailConfig.get_settings()
        
        # 如果未开启SMTP，或配置不完整，返回失败
        if not email_config.enable_smtp or not email_config.smtp_server:
            logger.error("SMTP未配置或未启用，邮件发送失败")
            if not fail_silently:
                raise ValueError("SMTP配置未启用或不完整")
            return False
        
        # 使用配置中的发件人邮箱（如果未指定）
        if from_email is None:
            if email_config.sender_name:
                from_email = f"{email_config.sender_name} <{email_config.sender_email}>"
            else:
                from_email = email_config.sender_email
        
        # 获取当前Django设置中的EMAIL_*配置
        current_email_host = getattr(settings, 'EMAIL_HOST', None)
        current_email_port = getattr(settings, 'EMAIL_PORT', None)
        current_email_host_user = getattr(settings, 'EMAIL_HOST_USER', None)
        current_email_host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
        current_email_use_tls = getattr(settings, 'EMAIL_USE_TLS', None)
        current_email_use_ssl = getattr(settings, 'EMAIL_USE_SSL', None)
        current_email_backend = getattr(settings, 'EMAIL_BACKEND', None)
        
        # 临时应用数据库中的配置
        settings.EMAIL_HOST = email_config.smtp_server
        settings.EMAIL_PORT = email_config.smtp_port
        settings.EMAIL_USE_TLS = email_config.security_type == 'tls'
        settings.EMAIL_USE_SSL = email_config.security_type == 'ssl'
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        
        if email_config.require_authentication:
            settings.EMAIL_HOST_USER = email_config.smtp_username
            settings.EMAIL_HOST_PASSWORD = email_config.smtp_password
        else:
            settings.EMAIL_HOST_USER = ''
            settings.EMAIL_HOST_PASSWORD = ''
        
        try:
            # 使用Django的send_mail函数发送邮件
            sent = django_send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=fail_silently
            )
            
            if sent:
                logger.info(f"成功发送邮件到: {', '.join(recipient_list)}")
                return True
            else:
                logger.error(f"邮件发送失败，收件人: {', '.join(recipient_list)}")
                return False
                
        finally:
            # 恢复原来的设置
            if current_email_host is not None:
                settings.EMAIL_HOST = current_email_host
            if current_email_port is not None:
                settings.EMAIL_PORT = current_email_port
            if current_email_host_user is not None:
                settings.EMAIL_HOST_USER = current_email_host_user
            if current_email_host_password is not None:
                settings.EMAIL_HOST_PASSWORD = current_email_host_password
            if current_email_use_tls is not None:
                settings.EMAIL_USE_TLS = current_email_use_tls
            if current_email_use_ssl is not None:
                settings.EMAIL_USE_SSL = current_email_use_ssl
            if current_email_backend is not None:
                settings.EMAIL_BACKEND = current_email_backend
            
    except Exception as e:
        logger.exception(f"发送邮件过程中发生错误: {str(e)}")
        if not fail_silently:
            raise
        return False

def send_verification_code(email, code, fail_silently=False):
    """
    发送验证码邮件
    
    参数:
        email (str): 收件人邮箱
        code (str): 验证码
        fail_silently (bool, optional): 是否静默失败。默认为False
        
    返回:
        bool: 发送成功返回True，失败返回False
    """
    subject = "【GameHub】验证码"
    
    # 纯文本邮件内容
    message = f"""
    您正在进行GameHub账号验证，验证码为：{code}
    
    验证码有效期为10分钟，请勿将验证码泄露给他人。
    如非本人操作，请忽略此邮件。
    
    GameHub团队
    """
    
    # HTML邮件内容
    html_message = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 5px;">
        <h2 style="color: #333;">GameHub验证码</h2>
        <p style="color: #666; line-height: 1.6;">您好，</p>
        <p style="color: #666; line-height: 1.6;">您正在进行GameHub账号验证，验证码为：</p>
        <div style="background-color: #f9f9f9; padding: 10px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 15px 0; border-radius: 4px;">
            {code}
        </div>
        <p style="color: #666; line-height: 1.6;">验证码有效期为10分钟，请勿将验证码泄露给他人。</p>
        <p style="color: #666; line-height: 1.6;">如非本人操作，请忽略此邮件。</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
        <p style="color: #999; font-size: 12px;">&copy; GameHub团队</p>
    </div>
    """
    
    return send_mail(
        subject=subject,
        message=message,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=fail_silently
    )

def test_smtp_connection():
    """
    测试SMTP连接，返回连接结果
    
    返回:
        dict: 包含连接测试结果的字典，格式为：
            {
                'success': bool,  # 连接是否成功
                'message': str,   # 成功或错误消息
                'details': list   # 详细日志
            }
    """
    logs = []
    
    try:
        # 获取邮件配置
        email_config = EmailConfig.get_settings()
        
        # 检查配置完整性
        if not email_config.enable_smtp:
            return {
                'success': False,
                'message': 'SMTP服务未启用',
                'details': logs
            }
        
        if not email_config.smtp_server:
            return {
                'success': False,
                'message': 'SMTP服务器地址未配置',
                'details': logs
            }
        
        # 记录配置信息
        logs.append(f"SMTP服务器: {email_config.smtp_server}")
        logs.append(f"SMTP端口: {email_config.smtp_port}")
        logs.append(f"安全类型: {email_config.security_type}")
        
        # 尝试连接SMTP服务器
        if email_config.security_type == 'ssl':
            logs.append("使用SSL连接")
            context = ssl.create_default_context()
            # 添加兼容性设置
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            server = smtplib.SMTP_SSL(
                email_config.smtp_server,
                email_config.smtp_port,
                context=context,
                timeout=30
            )
        else:
            logs.append("使用普通连接")
            server = smtplib.SMTP(
                email_config.smtp_server,
                email_config.smtp_port,
                timeout=30
            )
            
            if email_config.security_type == 'tls':
                logs.append("启用TLS")
                server.starttls()
                
        # 尝试登录
        if email_config.require_authentication:
            logs.append(f"尝试使用用户名 {email_config.smtp_username} 登录")
            server.login(email_config.smtp_username, email_config.smtp_password)
            logs.append("登录成功")
        
        # 测试连接
        server.ehlo_or_helo_if_needed()
        logs.append("连接测试成功")
        
        # 关闭连接
        server.quit()
        
        return {
            'success': True,
            'message': 'SMTP连接测试成功',
            'details': logs
        }
        
    except Exception as e:
        logs.append(f"连接测试失败: {str(e)}")
        logger.exception("SMTP连接测试失败")
        
        return {
            'success': False,
            'message': f'SMTP连接失败: {str(e)}',
            'details': logs
        } 