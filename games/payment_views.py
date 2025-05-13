from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import json
import logging

from core.models import SubscriptionPlan, PaymentGateway, Subscription, PaymentTransaction

logger = logging.getLogger('payment')

@login_required
def subscription_plans(request):
    """会员计划选择页面"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    
    # 获取用户当前订阅
    user_subscription = Subscription.objects.filter(
        user=request.user, 
        status__in=['active', 'trial']
    ).first()
    
    context = {
        'plans': plans,
        'current_subscription': user_subscription,
    }
    
    return render(request, 'games/payment/plan_selection.html', context)

@login_required
def checkout(request, plan_id):
    """结账页面"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    
    # 获取可用的支付网关
    gateways = PaymentGateway.objects.filter(is_active=True).order_by('display_order')
    
    # 根据计划周期计算结束日期
    start_date = timezone.now()
    end_date = start_date
    
    if plan.period == 'monthly':
        end_date = start_date + timedelta(days=30)
    elif plan.period == 'quarterly':
        end_date = start_date + timedelta(days=90)
    elif plan.period == 'yearly':
        end_date = start_date + timedelta(days=365)
    
    context = {
        'plan': plan,
        'gateways': gateways,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'games/payment/checkout.html', context)

@login_required
def payment_method(request, plan_id, gateway_id):
    """支付方式处理页面"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    gateway = get_object_or_404(PaymentGateway, id=gateway_id, is_active=True)
    
    # 创建待处理的订阅记录
    start_date = timezone.now()
    
    # 根据计划周期计算结束日期
    if plan.period == 'monthly':
        end_date = start_date + timedelta(days=30)
    elif plan.period == 'quarterly':
        end_date = start_date + timedelta(days=90)
    elif plan.period == 'yearly':
        end_date = start_date + timedelta(days=365)
    else:  # one_time
        end_date = start_date + timedelta(days=30)  # 默认30天
    
    # 检查是否已有相同计划的待处理订阅
    existing = Subscription.objects.filter(
        user=request.user,
        plan=plan,
        status='pending'
    ).first()
    
    if existing:
        subscription = existing
        subscription.start_date = start_date
        subscription.end_date = end_date
        subscription.payment_gateway = gateway
        subscription.save()
    else:
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status='pending',
            start_date=start_date,
            end_date=end_date,
            payment_gateway=gateway,
            auto_renew=(plan.period != 'one_time')  # 非一次性计划默认自动续费
        )
    
    # 创建交易记录
    transaction = PaymentTransaction.objects.create(
        user=request.user,
        subscription=subscription,
        gateway=gateway,
        amount=plan.price,
        currency='USD',  # 使用美元
        status='pending',
        transaction_type='subscription'
    )
    
    # 根据不同的支付网关类型处理支付
    if gateway.gateway_type == 'paypal':
        return redirect(reverse('games:paypal_payment', args=[transaction.id]))
    elif gateway.gateway_type == 'alipay':
        return redirect(reverse('games:alipay_payment', args=[transaction.id]))
    elif gateway.gateway_type == 'wechat':
        return redirect(reverse('games:wechat_payment', args=[transaction.id]))
    elif gateway.gateway_type == 'stripe':
        return redirect(reverse('games:stripe_payment', args=[transaction.id]))
    else:
        # 不支持的支付网关
        return redirect(reverse('games:payment_error'))

@login_required
def payment_success(request):
    """支付成功页面"""
    transaction_id = request.GET.get('transaction_id')
    if transaction_id:
        transaction = get_object_or_404(PaymentTransaction, id=transaction_id, user=request.user)
        context = {
            'transaction': transaction,
            'subscription': transaction.subscription
        }
    else:
        context = {}
    
    return render(request, 'games/payment/payment_success.html', context)

@login_required
def payment_cancel(request):
    """支付取消页面"""
    transaction_id = request.GET.get('transaction_id')
    if transaction_id:
        transaction = get_object_or_404(PaymentTransaction, id=transaction_id, user=request.user)
        
        # 将交易标记为已取消
        transaction.status = 'cancelled'
        transaction.save()
        
        context = {
            'transaction': transaction
        }
    else:
        context = {}
    
    return render(request, 'games/payment/payment_cancel.html', context)

@login_required
def payment_error(request):
    """支付错误页面"""
    error_message = request.GET.get('error', _('支付处理过程中发生错误'))
    transaction_id = request.GET.get('transaction_id')
    
    context = {
        'error_message': error_message
    }
    
    if transaction_id:
        transaction = get_object_or_404(PaymentTransaction, id=transaction_id, user=request.user)
        context['transaction'] = transaction
    
    return render(request, 'games/payment/payment_error.html', context)

# 各支付网关的处理视图示例
@login_required
def paypal_payment(request, transaction_id):
    """PayPal支付处理"""
    transaction = get_object_or_404(PaymentTransaction, id=transaction_id, user=request.user)
    gateway = transaction.gateway
    
    # 这里只是示例，实际实现需要使用PayPal SDK
    context = {
        'transaction': transaction,
        'gateway': gateway,
        'client_id': gateway.config.get('client_id', ''),
        'environment': gateway.config.get('environment', 'sandbox'),
        'return_url': request.build_absolute_uri(reverse('games:payment_success')) + f'?transaction_id={transaction.id}',
        'cancel_url': request.build_absolute_uri(reverse('games:payment_cancel')) + f'?transaction_id={transaction.id}',
    }
    
    return render(request, 'games/payment/paypal_payment.html', context)

@csrf_exempt
def paypal_webhook(request):
    """PayPal Webhook处理"""
    if request.method == 'POST':
        payload = request.body.decode('utf-8')
        logger.info(f'Received PayPal webhook: {payload}')
        
        # 这里需要验证PayPal IPN消息的真实性
        # 然后更新对应的订阅和交易状态
        
        return HttpResponse(status=200)
    return HttpResponse(status=400)

# 其他支付网关的处理视图将类似实现 