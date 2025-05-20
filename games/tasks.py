from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models_payment import (
    MembershipPayment, PaymentNotification,
    PaymentMethod, PaymentTemplate
)
import logging
import json

logger = logging.getLogger('payment_tasks')

@shared_task
def check_payment_timeouts():
    """检查并处理超时支付"""
    try:
        # 获取所有未完成的支付
        pending_payments = MembershipPayment.objects.filter(
            status__in=['waiting', 'pending'],
            timeout_at__lt=timezone.now()
        )
        
        timeout_count = 0
        for payment in pending_payments:
            if payment.check_timeout():
                timeout_count += 1
        
        logger.info(f"Processed {timeout_count} timed out payments")
        return timeout_count
    except Exception as e:
        logger.error(f"Error checking payment timeouts: {str(e)}", exc_info=True)
        raise 

@shared_task(bind=True, max_retries=3)
def send_payment_notification(self, notification_id):
    """异步发送支付通知"""
    try:
        notification = PaymentNotification.objects.get(id=notification_id)
        
        if notification.notification_type == 'email':
            # 获取对应的模板
            template_code = None
            if notification.payment.status == 'confirmed':
                template_code = 'payment_confirmed'
            elif notification.payment.status == 'rejected':
                template_code = 'payment_rejected'
            elif notification.payment.status == 'timeout':
                template_code = 'payment_timeout'
            
            template = PaymentTemplate.get_template(template_code, 'email')
            
            if template:
                # 使用模板的HTML内容
                html_message = template.render_content({
                    'payment': notification.payment,
                    'user': notification.payment.user,
                    'membership': notification.payment.membership
                })
            else:
                # 使用默认模板
                html_message = render_to_string('games/email/payment_notification.html', {
                    'payment': notification.payment,
                    'content': notification.content,
                })
            
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=notification.subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient],
                html_message=html_message,
                fail_silently=False,
            )
        elif notification.notification_type == 'webhook':
            # 获取webhook模板
            template = PaymentTemplate.get_template('payment_webhook', 'webhook')
            if template:
                # 使用模板内容发送webhook
                webhook_content = template.render_content({
                    'payment': notification.payment,
                    'user': notification.payment.user,
                    'membership': notification.payment.membership
                })
                # TODO: 实现webhook发送逻辑
                pass
        elif notification.notification_type == 'sms':
            # 获取短信模板
            template = PaymentTemplate.get_template('payment_sms', 'sms')
            if template:
                # 使用模板内容发送短信
                sms_content = template.render_content({
                    'payment': notification.payment,
                    'user': notification.payment.user,
                    'membership': notification.payment.membership
                })
                # TODO: 实现短信发送逻辑
                pass
        
        # 更新通知状态
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.save()
        
        logger.info(f"Payment notification sent: ID={notification.id}")
        return True
        
    except PaymentNotification.DoesNotExist:
        logger.error(f"Payment notification not found: ID={notification_id}")
        return False
    except Exception as e:
        logger.error(f"Error sending payment notification: {str(e)}", exc_info=True)
        # 更新通知状态为失败
        try:
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save()
        except:
            pass
        # 重试任务
        self.retry(exc=e, countdown=300)  # 5分钟后重试

@shared_task
def process_payment_notifications():
    """处理待发送的支付通知"""
    try:
        # 获取所有待发送的通知
        pending_notifications = PaymentNotification.objects.filter(
            status='pending',
            created_at__gte=timezone.now() - timezone.timedelta(days=1)  # 只处理最近24小时的通知
        )
        
        sent_count = 0
        for notification in pending_notifications:
            # 启动异步发送任务
            send_payment_notification.delay(notification.id)
            sent_count += 1
        
        logger.info(f"Queued {sent_count} payment notifications for sending")
        return sent_count
    except Exception as e:
        logger.error(f"Error processing payment notifications: {str(e)}", exc_info=True)
        raise 