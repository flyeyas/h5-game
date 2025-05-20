from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.views.generic import TemplateView, FormView, DetailView, ListView
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.db import transaction
from datetime import timedelta
from django import forms
import logging
import json

from plans.models import Plan, UserPlan
from payments import RedirectNeeded
from payments.forms import PaymentForm
from .models import Membership, UserProfile
from .models_payment import (
    MembershipPlan, MembershipPayment, PaymentMethod, 
    PaymentAttempt, PaymentInvoice, PaymentStatistics
)
from .payment_utils import provider_factory
from django.db import models

# 设置日志记录器
logger = logging.getLogger('payment_process')


class PaymentMethodForm(forms.Form):
    """支付方式选择表单"""
    payment_method = forms.ChoiceField(
        label=_('Payment Method'),
        choices=[],
        widget=forms.RadioSelect
    )
    
    def __init__(self, *args, **kwargs):
        payment_methods = kwargs.pop('payment_methods', None)
        super().__init__(*args, **kwargs)
        
        if payment_methods is None:
            payment_methods = PaymentMethod.objects.filter(is_active=True)
            
        self.fields['payment_method'].choices = [(m.code, m.name) for m in payment_methods]


class BillingInformationForm(forms.Form):
    """账单信息表单"""
    billing_first_name = forms.CharField(
        label=_('First Name'),
        max_length=100
    )
    billing_last_name = forms.CharField(
        label=_('Last Name'),
        max_length=100
    )
    billing_address = forms.CharField(
        label=_('Address'),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    billing_city = forms.CharField(
        label=_('City'),
        max_length=100,
        required=False
    )
    billing_country = forms.CharField(
        label=_('Country'),
        max_length=2,
        required=False
    )
    billing_postcode = forms.CharField(
        label=_('Postal Code'),
        max_length=20,
        required=False
    )
    billing_company = forms.CharField(
        label=_('Company'),
        max_length=100,
        required=False
    )
    tax_id = forms.CharField(
        label=_('Tax ID'),
        max_length=50,
        required=False
    )


def get_payment_host():
    """获取支付主机配置"""
    return PaymentMethod.get_payment_host()


@login_required
def process_payment(request, membership_id):
    """
    处理会员订阅支付
    """
    membership = get_object_or_404(Membership, id=membership_id, is_active=True)
    # 获取全局支付配置
    global_config = PaymentMethod.get_global_config()
    payment_host = get_payment_host()
    # 获取或创建关联的Plan
    membership_plan, created = MembershipPlan.objects.get_or_create(
        membership=membership,
        defaults={
            'plan': Plan.objects.get_or_create(
                name=membership.name,
                defaults={
                    'description': membership.description,
                    'customizable': False,
                    'available': True,
                    'visible': True,
                    'default': membership.level == 'free',
                    'created': timezone.now(),
                    'url': '',
                    'quotas': {}
                }
            )[0]
        }
    )
    # 创建或更新用户计划
    user_plan, created = UserPlan.objects.get_or_create(
        user=request.user,
        defaults={
            'plan': membership_plan.plan,
            'active': False,
            'expire': None
        }
    )
    if not created:
        user_plan.plan = membership_plan.plan
        user_plan.save()
    # 创建支付记录
    with transaction.atomic():
        payment = MembershipPayment.objects.create(
            user=request.user,
            membership=membership,
            user_plan=user_plan,
            variant='default',  # 将在选择支付方式时更新
            description=_('Membership: {}').format(membership.name),
            total=membership.price,
            tax=global_config['tax'],
            currency=global_config['currency'],
            billing_first_name=request.user.first_name or request.user.username,
            billing_last_name=request.user.last_name or '',
            billing_email=request.user.email,
        )
        
        # 设置支付主机
        payment.host = payment_host
        
        # 记录IP信息
        payment.record_ip_info(request)
        
        # 执行欺诈检查
        fraud_status = payment.check_fraud(request)
        
        # 如果欺诈风险过高，拒绝支付
        if fraud_status == 'rejected':
            messages.error(request, _('Payment was rejected due to security reasons. Please contact support.'))
            return redirect('games:payment_failed', payment_id=payment.id)
        
        # 记录日志
        logger.info(
            f"Payment initiated: ID={payment.id}, "
            f"User={request.user.username}, "
            f"Membership={membership.name}, "
            f"Amount={payment.total} {payment.currency}"
        )
    
    # 重定向到支付方式选择页面
    return redirect('games:payment_method_selection', payment_id=payment.id)


@method_decorator(login_required, name='dispatch')
class PaymentMethodSelectionView(FormView):
    """支付方式选择页面"""
    template_name = 'games/membership/payment_form.html'
    form_class = PaymentMethodForm
    
    def get_success_url(self):
        return reverse('games:payment_process', kwargs={'payment_id': self.payment.id})
    
    def dispatch(self, request, *args, **kwargs):
        payment_id = kwargs.get('payment_id')
        try:
            self.payment = get_object_or_404(MembershipPayment, id=payment_id, user=request.user)
            
            # 如果已经完成支付，直接跳转到成功页面
            if self.payment.status == 'confirmed':
                return redirect('games:payment_success', payment_id=payment_id)
            
            # 如果已经拒绝，跳转到失败页面
            if self.payment.status == 'rejected':
                return redirect('games:payment_failed', payment_id=payment_id)
            
            return super().dispatch(request, *args, **kwargs)
        except MembershipPayment.DoesNotExist:
            messages.error(request, _('Payment not found.'))
            return redirect('games:subscription')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # 仅获取有效的支付方式
        active_methods = PaymentMethod.objects.filter(is_active=True).order_by('sort_order')
        kwargs['payment_methods'] = active_methods
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment'] = self.payment
        context['membership'] = self.payment.membership
        context['form_action'] = self.request.path
        
        # 获取可用的支付方式
        context['payment_methods'] = PaymentMethod.objects.filter(is_active=True).order_by('sort_order')
        
        return context
    
    def form_valid(self, form):
        payment_method_code = form.cleaned_data['payment_method']
        
        try:
            payment_method = PaymentMethod.objects.get(code=payment_method_code, is_active=True)
        except PaymentMethod.DoesNotExist:
            messages.error(self.request, _('Selected payment method is not available.'))
            return self.form_invalid(form)
        
        # 更新支付信息
        self.payment.variant = payment_method_code
        self.payment.payment_method_code = payment_method_code
        self.payment.save(update_fields=['variant', 'payment_method_code'])
        
        # 记录支付尝试
        PaymentAttempt.record_attempt(
            payment=self.payment,
            request=self.request,
            method_code=payment_method_code
        )
        
        # 记录日志
        logger.info(
            f"Payment method selected: ID={self.payment.id}, "
            f"User={self.request.user.username}, "
            f"Method={payment_method_code}"
        )
        
        return super().form_valid(form)


def get_payment_provider_class(payment):
    """获取支付提供商类"""
    try:
        # 使用自定义provider_factory从数据库获取支付提供商
        provider = provider_factory(payment.payment_method_code, payment)
        return provider.__class__, provider.provider_settings
    except Exception as e:
        logger.error(f"Error getting payment provider: {str(e)}", exc_info=True)
        
        # 返回默认提供商作为后备
        from payments.dummy import DummyProvider
        return DummyProvider, {}


@method_decorator(login_required, name='dispatch')
class PaymentProcessView(FormView):
    """支付处理页面"""
    template_name = 'games/membership/payment_process.html'
    form_class = PaymentForm
    
    def dispatch(self, request, *args, **kwargs):
        payment_id = kwargs.get('payment_id')
        try:
            self.payment = get_object_or_404(MembershipPayment, id=payment_id, user=request.user)
            
            # 如果支付方式尚未选择，重定向到支付方式选择页面
            if not self.payment.payment_method_code:
                return redirect('games:payment_method_selection', payment_id=payment_id)
            
            # 如果已经完成支付，直接跳转到成功页面
            if self.payment.status == 'confirmed':
                return redirect('games:payment_success', payment_id=payment_id)
            
            # 如果已经拒绝，跳转到失败页面
            if self.payment.status == 'rejected':
                return redirect('games:payment_failed', payment_id=payment_id)
            
            return super().dispatch(request, *args, **kwargs)
        except MembershipPayment.DoesNotExist:
            messages.error(request, _('Payment not found.'))
            return redirect('games:subscription')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        
        # 使用自定义provider_factory获取提供商
        provider = provider_factory(self.payment.payment_method_code, self.payment)
        
        kwargs['payment'] = self.payment
        kwargs['provider'] = provider
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment'] = self.payment
        context['membership'] = self.payment.membership
        return context
    
    def form_valid(self, form):
        try:
            form.save()
            return HttpResponseRedirect(self.payment.get_success_url())
        except RedirectNeeded as redirect_to:
            return HttpResponseRedirect(str(redirect_to))
        except Exception as e:
            # 记录支付尝试失败
            attempt = PaymentAttempt.objects.filter(
                payment=self.payment, 
                status='pending'
            ).order_by('-created_at').first()
            
            if attempt:
                attempt.status = 'failed'
                attempt.error_message = str(e)
                attempt.save()
            
            # 更新支付记录
            self.payment.failure_reason = str(e)
            self.payment.retry_count += 1
            self.payment.save(update_fields=['failure_reason', 'retry_count'])
            
            # 记录日志
            logger.error(
                f"Payment processing error: ID={self.payment.id}, "
                f"User={self.request.user.username}, "
                f"Method={self.payment.payment_method_code}, "
                f"Error={str(e)}"
            )
            
            messages.error(
                self.request, 
                _('An error occurred during payment processing. Please try again or choose another payment method.')
            )
            return redirect('games:payment_failed', payment_id=self.payment.id)


@method_decorator(login_required, name='dispatch')
class PaymentSuccessView(DetailView):
    """支付成功页面"""
    model = MembershipPayment
    template_name = 'games/membership/payment_success.html'
    context_object_name = 'payment'
    pk_url_kwarg = 'payment_id'
    
    def get_queryset(self):
        return MembershipPayment.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['membership'] = self.object.membership
        context['expiry_date'] = self.request.user.profile.membership_expiry
        
        # 如果存在发票，添加到上下文
        try:
            context['invoice'] = self.object.invoice
        except PaymentInvoice.DoesNotExist:
            pass
        
        # 更新任何挂起的支付尝试
        pending_attempts = PaymentAttempt.objects.filter(
            payment=self.object, 
            status='pending'
        )
        
        for attempt in pending_attempts:
            attempt.status = 'success'
            attempt.save()
        
        return context


@method_decorator(login_required, name='dispatch')
class PaymentFailedView(DetailView):
    """支付失败页面"""
    model = MembershipPayment
    template_name = 'games/membership/payment_failed.html'
    context_object_name = 'payment'
    pk_url_kwarg = 'payment_id'
    
    def get_queryset(self):
        return MembershipPayment.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['membership'] = self.object.membership
        
        # 构建错误信息
        error_message = self.object.failure_reason
        
        if not error_message:
            if self.object.fraud_status == 'rejected':
                error_message = _('Payment was rejected due to security reasons.')
            else:
                error_message = _('Payment failed. Please try again or choose another payment method.')
        
        context['error_message'] = error_message
        context['can_retry'] = self.object.status != 'confirmed' and self.object.fraud_status != 'rejected'
        
        # 获取其他支付方式
        context['payment_methods'] = PaymentMethod.objects.filter(
            is_active=True
        ).exclude(
            code=self.object.payment_method_code
        ).order_by('sort_order')
        
        return context


@login_required
def retry_payment(request, payment_id):
    """重试支付"""
    payment = get_object_or_404(MembershipPayment, id=payment_id, user=request.user)
    
    # 如果已经完成或被拒绝，不允许重试
    if payment.status == 'confirmed':
        messages.info(request, _('This payment has already been completed.'))
        return redirect('games:payment_success', payment_id=payment_id)
    
    if payment.fraud_status == 'rejected':
        messages.error(request, _('This payment cannot be retried due to security reasons.'))
        return redirect('games:payment_failed', payment_id=payment_id)
    
    # 重置支付状态
    payment.status = 'waiting'
    payment.save(update_fields=['status'])
    
    # 记录日志
    logger.info(
        f"Payment retry: ID={payment.id}, "
        f"User={request.user.username}, "
        f"Retry Count={payment.retry_count}"
    )
    
    # 如果已选择支付方式，继续处理支付
    if payment.payment_method_code:
        return redirect('games:payment_process', payment_id=payment_id)
    else:
        return redirect('games:payment_method_selection', payment_id=payment_id)


@method_decorator(login_required, name='dispatch')
class PaymentHistoryView(ListView):
    """支付历史记录视图"""
    model = MembershipPayment
    template_name = 'games/membership/payment_history.html'
    context_object_name = 'payments'
    paginate_by = 10
    
    def get_queryset(self):
        return MembershipPayment.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


@method_decorator(login_required, name='dispatch')
class PaymentInvoiceDetailView(DetailView):
    """支付发票详情视图"""
    model = PaymentInvoice
    template_name = 'games/membership/payment_invoice.html'
    context_object_name = 'invoice'
    pk_url_kwarg = 'invoice_id'
    
    def get_queryset(self):
        return PaymentInvoice.objects.filter(payment__user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment'] = self.object.payment
        context['membership'] = self.object.payment.membership
        return context


@login_required
def download_invoice(request, invoice_id):
    """下载发票PDF"""
    invoice = get_object_or_404(PaymentInvoice, id=invoice_id, payment__user=request.user)
    
    # 如果未生成PDF文件，则生成
    if not invoice.pdf_file:
        # 在这里添加生成PDF的代码
        # 可以使用weasyprint或reportlab等库
        # 这里简化处理
        pass
    
    if invoice.pdf_file:
        return redirect(invoice.pdf_file.url)
    else:
        messages.error(request, _('Invoice PDF is not available for download.'))
        return redirect('games:payment_invoice_detail', invoice_id=invoice_id)


@login_required
def change_payment_method(request, payment_id):
    """更改支付方式"""
    payment = get_object_or_404(MembershipPayment, id=payment_id, user=request.user)
    
    # 如果已经完成或被拒绝，不允许更改
    if payment.status == 'confirmed':
        messages.info(request, _('This payment has already been completed.'))
        return redirect('games:payment_success', payment_id=payment_id)
    
    if payment.fraud_status == 'rejected':
        messages.error(request, _('This payment cannot be modified due to security reasons.'))
        return redirect('games:payment_failed', payment_id=payment_id)
    
    # 重定向到支付方式选择页面
    return redirect('games:payment_method_selection', payment_id=payment_id)


@method_decorator(login_required, name='dispatch')
class PaymentStatisticsView(TemplateView):
    """支付统计视图"""
    template_name = 'games/membership/payment_statistics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取日期范围
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        
        if end_date:
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        # 获取统计数据
        stats = PaymentStatistics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        # 计算汇总数据
        summary = stats.aggregate(
            total_payments=models.Sum('total_payments'),
            successful_payments=models.Sum('successful_payments'),
            failed_payments=models.Sum('failed_payments'),
            total_amount=models.Sum('total_amount'),
            successful_amount=models.Sum('successful_amount'),
            new_members=models.Sum('new_members'),
            renewals=models.Sum('renewals')
        )
        
        # 计算转化率
        conversion_rate = PaymentStatistics.get_conversion_rate(start_date, end_date)
        
        # 准备图表数据
        chart_data = {
            'dates': [stat.date.strftime('%Y-%m-%d') for stat in stats],
            'payments': [stat.total_payments for stat in stats],
            'amounts': [float(stat.total_amount) for stat in stats],
            'new_members': [stat.new_members for stat in stats],
            'renewals': [stat.renewals for stat in stats]
        }
        
        context.update({
            'stats': stats,
            'summary': summary,
            'conversion_rate': conversion_rate,
            'chart_data': json.dumps(chart_data),
            'start_date': start_date,
            'end_date': end_date,
            'date_range': (end_date - start_date).days + 1
        })
        
        return context