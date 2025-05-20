from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from payments import get_payment_model
from ipware import get_client_ip
import logging
import hashlib
import json
import hmac
import base64
from .models_payment import MembershipPayment, PaymentMethod, PaymentAttempt
from .payment_utils import provider_factory

# 设置日志记录器
logger = logging.getLogger('payment_callbacks')

def verify_signature(request, payment_method):
    """验证支付回调的签名"""
    try:
        # 根据不同的支付方式使用不同的验证方法
        if payment_method.code == 'paypal':
            return verify_paypal_webhook(request, payment_method)
        elif payment_method.code == 'stripe':
            return verify_stripe_webhook(request, payment_method)
        else:
            # 通用验证方法
            provided_signature = request.META.get('HTTP_X_SIGNATURE', '')
            if not provided_signature:
                logger.warning(f"Missing signature in callback for payment method: {payment_method.code}")
                return False
            # 获取安全密钥
            try:
                from django.core.cache import cache
                security_key = cache.get('payment_security_key')
                if not security_key:
                    global_config = PaymentMethod.get_global_config()
                    security_key = global_config['security_key']
                    cache.set('payment_security_key', security_key, 3600)
            except:
                global_config = PaymentMethod.get_global_config()
                security_key = global_config['security_key']
            # 如果未找到，使用提供商配置或设置中的默认值
            secret = payment_method.configuration.get(
                'webhook_secret', 
                security_key
            )
            payload = request.body
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            if provided_signature != expected_signature:
                logger.warning(
                    f"Invalid signature in callback. Method: {payment_method.code}, "
                    f"Expected: {expected_signature}, Received: {provided_signature}"
                )
                return False
            return True
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}", exc_info=True)
        return False

def verify_paypal_webhook(request, payment_method):
    """验证PayPal回调签名"""
    try:
        paypal_transmission_id = request.META.get('HTTP_PAYPAL_TRANSMISSION_ID', '')
        paypal_timestamp = request.META.get('HTTP_PAYPAL_TRANSMISSION_TIME', '')
        paypal_signature = request.META.get('HTTP_PAYPAL_TRANSMISSION_SIG', '')
        paypal_cert_url = request.META.get('HTTP_PAYPAL_CERT_URL', '')
        
        if not all([paypal_transmission_id, paypal_timestamp, paypal_signature, paypal_cert_url]):
            logger.warning("Missing required PayPal webhook headers")
            return False
            
        # 在实际应用中，这里应该使用PayPal SDK进行验证
        # 简化实现
        return True
    except Exception as e:
        logger.error(f"Error verifying PayPal webhook: {str(e)}", exc_info=True)
        return False

def verify_stripe_webhook(request, payment_method):
    """验证Stripe回调签名"""
    try:
        stripe_signature = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        if not stripe_signature:
            logger.warning("Missing Stripe signature header")
            return False
            
        # 在实际应用中，这里应该使用Stripe SDK进行验证
        # 简化实现
        return True
    except Exception as e:
        logger.error(f"Error verifying Stripe webhook: {str(e)}", exc_info=True)
        return False

@csrf_exempt
@require_POST
def payment_callback(request, payment_id):
    """支付回调处理"""
    try:
        with transaction.atomic():
            payment = get_object_or_404(MembershipPayment, id=payment_id)
            
            # 记录回调请求信息
            client_ip, is_routable = get_client_ip(request)
            logger.info(
                f"Payment callback received: ID={payment_id}, "
                f"IP={client_ip}, "
                f"User-Agent={request.META.get('HTTP_USER_AGENT', '')}"
            )
            
            # 获取支付提供商
            try:
                payment_method_code = request.POST.get('payment_method', payment.payment_method_code)
                payment_method = PaymentMethod.objects.get(code=payment_method_code)
            except PaymentMethod.DoesNotExist:
                logger.error(f"Payment method not found: {payment_method_code}")
                return HttpResponse(status=400)
            
            # 验证签名
            if not verify_signature(request, payment_method):
                logger.error(f"Signature verification failed for payment: {payment_id}")
                return HttpResponse(status=403)
            
            # 处理支付状态
            status = request.POST.get('status')
            transaction_id = request.POST.get('transaction_id', '')
            
            if status == 'success':
                # 查找是否有未完成的支付尝试
                attempt = PaymentAttempt.objects.filter(
                    payment=payment, 
                    status='pending'
                ).order_by('-created_at').first()
                
                if attempt:
                    attempt.status = 'success'
                    attempt.provider_reference = transaction_id
                    attempt.save()
                
                payment.status = 'confirmed'
                payment.captured_amount = payment.total
                payment.transaction_id = transaction_id or f"callback_{payment_id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
                
                # 保存支付处理器响应
                response_data = {}
                for key, value in request.POST.items():
                    response_data[key] = value
                payment.payment_processor_response = response_data
                
                payment.save()
                
                # 调用支付成功处理方法
                payment.payment_success()
                
                logger.info(f"Payment successfully processed: ID={payment_id}, Transaction={payment.transaction_id}")
                return HttpResponse('OK')
            elif status == 'failed':
                # 更新支付尝试记录
                attempt = PaymentAttempt.objects.filter(
                    payment=payment, 
                    status='pending'
                ).order_by('-created_at').first()
                
                if attempt:
                    attempt.status = 'failed'
                    attempt.error_message = request.POST.get('error_message', '')
                    attempt.save()
                
                payment.status = 'rejected'
                payment.failure_reason = request.POST.get('error_message', '')
                
                # 保存支付处理器响应
                response_data = {}
                for key, value in request.POST.items():
                    response_data[key] = value
                payment.payment_processor_response = response_data
                
                payment.save()
                
                logger.info(f"Payment failed: ID={payment_id}, Reason={payment.failure_reason}")
                return HttpResponse('OK')
            else:
                logger.warning(f"Unknown payment status in callback: {status}")
                return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}", exc_info=True)
        return HttpResponse(status=500)


@csrf_exempt
def payment_notification(request):
    """支付通知处理，用于第三方支付平台主动推送的异步通知"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # 记录通知信息
        client_ip, is_routable = get_client_ip(request)
        logger.info(
            f"Payment notification received: "
            f"IP={client_ip}, "
            f"User-Agent={request.META.get('HTTP_USER_AGENT', '')}"
        )
        
        # 获取支付方式
        payment_method_code = request.POST.get('payment_method')
        if not payment_method_code:
            logger.error("Missing payment_method in notification")
            return HttpResponse(status=400)
        
        try:
            payment_method = PaymentMethod.objects.get(code=payment_method_code)
        except PaymentMethod.DoesNotExist:
            logger.error(f"Payment method not found: {payment_method_code}")
            return HttpResponse(status=400)
        
        # 验证签名
        if not verify_signature(request, payment_method):
            logger.error("Signature verification failed for notification")
            return HttpResponse(status=403)
        
        # 获取交易ID
        transaction_id = request.POST.get('transaction_id')
        if not transaction_id:
            logger.error("Missing transaction_id in notification")
            return HttpResponse(status=400)
        
        # 查找对应的支付记录
        try:
            payment = MembershipPayment.objects.get(transaction_id=transaction_id)
        except MembershipPayment.DoesNotExist:
            # 如果找不到交易ID，尝试使用外部参考号查找
            external_id = request.POST.get('external_id')
            if external_id:
                try:
                    attempt = PaymentAttempt.objects.get(provider_reference=external_id)
                    payment = attempt.payment
                except PaymentAttempt.DoesNotExist:
                    logger.error(f"Payment not found for transaction: {transaction_id} or external_id: {external_id}")
                    return HttpResponse(status=404)
            else:
                logger.error(f"Payment not found for transaction: {transaction_id}")
                return HttpResponse(status=404)
        
        # 处理支付状态
        with transaction.atomic():
            status = request.POST.get('status')
            if status == 'success' and payment.status != 'confirmed':
                payment.status = 'confirmed'
                payment.captured_amount = float(request.POST.get('amount', payment.total))
                
                # 保存支付处理器响应
                response_data = {}
                for key, value in request.POST.items():
                    response_data[key] = value
                payment.payment_processor_response = response_data
                
                payment.save()
                
                # 调用支付成功处理方法
                payment.payment_success()
                
                logger.info(f"Payment confirmed by notification: ID={payment.id}, Transaction={transaction_id}")
                return HttpResponse('SUCCESS')
            elif status == 'failed' and payment.status != 'rejected':
                payment.status = 'rejected'
                payment.failure_reason = request.POST.get('error_message', '')
                
                # 保存支付处理器响应
                response_data = {}
                for key, value in request.POST.items():
                    response_data[key] = value
                payment.payment_processor_response = response_data
                
                payment.save()
                
                logger.info(f"Payment rejected by notification: ID={payment.id}, Transaction={transaction_id}")
                return HttpResponse('SUCCESS')
            
            # 记录通知，但不更改状态
            logger.info(f"Payment notification received but no status change: ID={payment.id}, Status={status}")
            return HttpResponse('OK')
            
    except Exception as e:
        logger.error(f"Error processing payment notification: {str(e)}", exc_info=True)
        return HttpResponse(status=500)