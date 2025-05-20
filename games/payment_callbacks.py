from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
import json
import logging
import hashlib
import hmac
from datetime import timedelta
from functools import wraps
from .models_payment import (
    MembershipPayment, PaymentAttempt, PaymentNotification,
    PaymentMethod
)

# 设置日志记录器
logger = logging.getLogger('payment_callbacks')

def verify_callback_signature(request, payment_method):
    """验证回调签名"""
    try:
        # 获取签名配置
        config = payment_method.configuration
        secret_key = config.get('webhook_secret')
        if not secret_key:
            logger.error(f"Missing webhook secret for payment method: {payment_method.code}")
            return False

        # 获取请求签名
        signature = request.headers.get('X-Payment-Signature')
        if not signature:
            logger.error("Missing payment signature in callback")
            return False

        # 计算签名
        payload = request.body
        expected_signature = hmac.new(
            secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying callback signature: {str(e)}", exc_info=True)
        return False

def handle_callback_retry(callback_id, max_retries=3, retry_delay=300):
    """处理回调重试"""
    retry_key = f'payment_callback_retry:{callback_id}'
    retry_count = cache.get(retry_key, 0)
    
    if retry_count >= max_retries:
        logger.error(f"Callback {callback_id} exceeded max retries")
        return False
    
    cache.set(retry_key, retry_count + 1, retry_delay)
    return True

def log_callback(request, payment_method, status='received'):
    """记录回调日志"""
    try:
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'body': request.body.decode() if request.body else None,
            'payment_method': payment_method.code,
            'status': status
        }
        logger.info(f"Payment callback: {json.dumps(log_data)}")
    except Exception as e:
        logger.error(f"Error logging callback: {str(e)}", exc_info=True)

@csrf_exempt
@require_POST
def payment_callback(request, payment_method_code):
    """处理支付回调"""
    try:
        # 获取支付方式
        payment_method = PaymentMethod.objects.get(code=payment_method_code, is_active=True)
    except PaymentMethod.DoesNotExist:
        logger.error(f"Invalid payment method code: {payment_method_code}")
        return HttpResponse(status=404)

    # 记录回调
    log_callback(request, payment_method)

    # 验证签名
    if not verify_callback_signature(request, payment_method):
        logger.error(f"Invalid signature for payment method: {payment_method_code}")
        return HttpResponse(status=403)

    try:
        # 解析回调数据
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        
        if not transaction_id or not status:
            logger.error(f"Missing required fields in callback data: {data}")
            return HttpResponse(status=400)

        # 查找支付记录
        try:
            payment = MembershipPayment.objects.get(
                transaction_id=transaction_id,
                payment_method_code=payment_method_code
            )
        except MembershipPayment.DoesNotExist:
            logger.error(f"Payment not found for transaction: {transaction_id}")
            return HttpResponse(status=404)

        # 处理支付状态更新
        with transaction.atomic():
            # 更新支付状态
            old_status = payment.status
            payment.status = status
            payment.payment_processor_response = data
            payment.save()

            # 记录支付尝试
            PaymentAttempt.objects.create(
                payment=payment,
                user=payment.user,
                payment_method_code=payment_method_code,
                status='success' if status == 'confirmed' else 'failed',
                provider_reference=transaction_id
            )

            # 如果支付成功，处理成功逻辑
            if status == 'confirmed':
                payment.payment_success()
                
                # 发送成功通知
                payment.send_payment_notification(
                    notification_type='email',
                    status='confirmed'
                )

            # 记录状态变化
            logger.info(
                f"Payment status updated: ID={payment.id}, "
                f"Old Status={old_status}, New Status={status}, "
                f"Transaction={transaction_id}"
            )

        return HttpResponse(status=200)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in callback data")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}", exc_info=True)
        
        # 处理重试
        callback_id = f"{payment_method_code}:{request.body.decode()}"
        if handle_callback_retry(callback_id):
            return HttpResponse(status=503)  # 服务暂时不可用，请求重试
        return HttpResponse(status=500)

def async_process_callback(callback_data):
    """异步处理支付回调"""
    from celery import shared_task
    
    @shared_task(bind=True, max_retries=3)
    def process_callback_task(self, callback_data):
        try:
            # 这里实现异步处理逻辑
            # 例如：发送通知、更新统计等
            pass
        except Exception as e:
            logger.error(f"Error in async callback processing: {str(e)}", exc_info=True)
            # 重试任务
            self.retry(exc=e, countdown=300)  # 5分钟后重试
    
    # 启动异步任务
    process_callback_task.delay(callback_data) 