from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.urls import reverse_lazy
from django import forms
import json
from django.http import HttpResponse
import csv
import xlsxwriter
from io import BytesIO
from datetime import datetime

from .models_payment import MembershipPayment, PaymentMethod, PaymentStatistics, PaymentNotification, PaymentTemplate
from .models import UserProfile


def is_admin(user):
    """检查用户是否是管理员"""
    return user.is_authenticated and user.is_staff


class PaymentMethodForm(forms.ModelForm):
    """支付方式表单"""
    class Meta:
        model = PaymentMethod
        fields = ['name', 'code', 'provider_class', 'is_active', 'sort_order', 'icon', 'description', 'configuration']
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'paypal, stripe, etc.'}),
            'configuration': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    configuration_json = forms.CharField(
        label=_('配置参数'),
        widget=forms.Textarea(attrs={'class': 'json-editor', 'rows': 8}),
        required=False,
        help_text=_('请输入有效的JSON配置参数')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 初始化JSON配置
        if self.instance.pk and self.instance.configuration:
            self.fields['configuration_json'].initial = json.dumps(
                self.instance.configuration, indent=4
            )
            
        # 如果是全局配置，则禁用某些字段
        if self.instance.pk and self.instance.code == 'global_config':
            self.fields['code'].disabled = True
            self.fields['provider_class'].disabled = True
            
            # 为全局配置添加特殊标记
            self.fields['configuration_json'].help_text = _(
                '全局安全配置，包含支付系统使用的安全密钥、盐值和欺诈检测阈值等配置。'
            )
    
    def clean_configuration_json(self):
        """验证JSON配置"""
        json_data = self.cleaned_data.get('configuration_json')
        if not json_data:
            return {}
        
        try:
            return json.loads(json_data)
        except json.JSONDecodeError:
            raise forms.ValidationError(_('请输入有效的JSON格式'))
    
    def clean(self):
        """表单整体验证"""
        cleaned_data = super().clean()
        
        # 将JSON配置转换为Python对象并保存
        if 'configuration_json' in cleaned_data:
            cleaned_data['configuration'] = cleaned_data.pop('configuration_json')
        
        # 如果是全局配置，则验证必要的安全字段
        if self.instance.pk and self.instance.code == 'global_config':
            configuration = cleaned_data.get('configuration', {})
            
            if not configuration.get('security_key'):
                self.add_error('configuration_json', _('全局配置需要security_key字段'))
                
            if not configuration.get('security_salt'):
                self.add_error('configuration_json', _('全局配置需要security_salt字段'))
                
            if 'fraud_threshold' not in configuration:
                self.add_error('configuration_json', _('全局配置需要fraud_threshold字段'))
            
        # 检查所选提供商的必填配置字段
        else:
            provider_class = cleaned_data.get('provider_class')
            configuration = cleaned_data.get('configuration', {})
            
            if provider_class == 'payments.paypal.PaypalProvider':
                if not configuration.get('client_id'):
                    self.add_error('configuration_json', _('PayPal配置需要client_id字段'))
                if not configuration.get('secret'):
                    self.add_error('configuration_json', _('PayPal配置需要secret字段'))
                    
            elif provider_class == 'payments.stripe.StripeProvider':
                if not configuration.get('api_key'):
                    self.add_error('configuration_json', _('Stripe配置需要api_key字段'))
                if not configuration.get('public_key'):
                    self.add_error('configuration_json', _('Stripe配置需要public_key字段'))
        
        return cleaned_data


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminPaymentListView(ListView):
    """管理员支付记录列表视图"""
    model = MembershipPayment
    template_name = 'admin/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MembershipPayment.objects.all().order_by('-created_at')
        
        # 搜索过滤
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(user__username__icontains=q) | 
                Q(user__email__icontains=q) | 
                Q(transaction_id__icontains=q) |
                Q(id__icontains=q)
            )
        
        # 状态过滤
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 添加支付统计信息
        all_payments = MembershipPayment.objects.all()
        context['total_count'] = all_payments.count()
        context['confirmed_count'] = all_payments.filter(status='confirmed').count()
        context['waiting_count'] = all_payments.filter(status='waiting').count()
        context['rejected_count'] = all_payments.filter(status='rejected').count()
        
        # 添加收入统计
        context['total_income'] = all_payments.filter(status='confirmed').aggregate(
            total=Sum('total')
        )['total'] or 0
        
        return context


@login_required
@user_passes_test(is_admin)
def admin_payment_confirm(request, payment_id):
    """管理员确认支付"""
    payment = get_object_or_404(MembershipPayment, id=payment_id)
    
    if payment.status != 'waiting':
        messages.error(request, _('This payment cannot be confirmed because its status is not waiting.'))
        return redirect('games:admin_payment_list')
    
    # 更新支付状态
    payment.status = 'confirmed'
    payment.captured_amount = payment.total
    if not payment.transaction_id:
        payment.transaction_id = f"manual_{payment_id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
    payment.save()
    
    # 调用支付成功处理方法
    payment.payment_success()
    
    messages.success(request, _('Payment has been confirmed successfully.'))
    return redirect('games:admin_payment_list')


@login_required
@user_passes_test(is_admin)
def admin_payment_reject(request, payment_id):
    """管理员拒绝支付"""
    payment = get_object_or_404(MembershipPayment, id=payment_id)
    
    if payment.status != 'waiting':
        messages.error(request, _('This payment cannot be rejected because its status is not waiting.'))
        return redirect('games:admin_payment_list')
    
    # 更新支付状态
    payment.status = 'rejected'
    payment.save()
    
    messages.success(request, _('Payment has been rejected successfully.'))
    return redirect('games:admin_payment_list')


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminPaymentMethodListView(ListView):
    """管理员支付方式列表视图"""
    model = PaymentMethod
    template_name = 'admin/payment_method_list.html'
    context_object_name = 'payment_methods'
    paginate_by = 20
    
    def get_queryset(self):
        # 排除全局配置
        queryset = PaymentMethod.objects.exclude(code='global_config')
        
        # 搜索过滤
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | 
                Q(code__icontains=q) | 
                Q(provider_class__icontains=q)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取全局配置
        try:
            global_config = PaymentMethod.objects.get(code='global_config')
            context['global_config'] = global_config
        except PaymentMethod.DoesNotExist:
            context['global_config'] = None
            
        # 获取已配置的提供商类
        configured_providers = set(PaymentMethod.objects.values_list('provider_class', flat=True))
        
        # 准备可用提供商列表
        provider_choices = PaymentMethod.PROVIDER_CHOICES
        
        # 分类提供商
        standard_providers = []
        custom_providers = []
        
        for provider_class, name in provider_choices:
            if 'dummy' in provider_class.lower() or 'paypal' in provider_class.lower() or 'stripe' in provider_class.lower():
                standard_providers.append({
                    'class': provider_class,
                    'name': name,
                    'configured': provider_class in configured_providers
                })
            else:
                custom_providers.append({
                    'class': provider_class,
                    'name': name,
                    'configured': provider_class in configured_providers
                })
        
        context['standard_providers'] = standard_providers
        context['custom_providers'] = custom_providers
        
        return context


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminPaymentMethodCreateView(CreateView):
    """管理员创建支付方式视图"""
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'admin/payment_method_form.html'
    success_url = reverse_lazy('games:admin_payment_method_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Payment Method')
        
        # 预设提供商
        provider_class = self.request.GET.get('provider')
        if provider_class:
            context['form'].initial['provider_class'] = provider_class
            
            # 根据提供商类型预设配置模板
            template_configs = {
                'payments.dummy.DummyProvider': {'auto_confirm': True},
                'payments.paypal.PaypalProvider': {
                    'client_id': '',
                    'secret': '',
                    'endpoint': 'https://api.sandbox.paypal.com',
                    'capture': True
                },
                'payments.stripe.StripeProvider': {
                    'api_key': '',
                    'public_key': ''
                },
                'payments.manual.ManualProvider': {
                    'instructions': 'Please transfer the payment to our bank account and upload the receipt.',
                    'account_details': 'Bank: Example Bank, Account: 1234567890, Name: Company Ltd',
                    'requires_admin_confirmation': True
                }
            }
            
            if provider_class in template_configs:
                context['form'].fields['configuration_json'].initial = json.dumps(
                    template_configs[provider_class], indent=4
                )
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Payment method has been created successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminPaymentMethodUpdateView(UpdateView):
    """管理员编辑支付方式视图"""
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'admin/payment_method_form.html'
    success_url = reverse_lazy('games:admin_payment_method_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Payment Method')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Payment method has been updated successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminPaymentMethodDeleteView(DeleteView):
    """管理员删除支付方式视图"""
    model = PaymentMethod
    template_name = 'admin/payment_method_confirm_delete.html'
    success_url = reverse_lazy('games:admin_payment_method_list')
    context_object_name = 'payment_method'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Payment method has been deleted successfully.'))
        return super().delete(request, *args, **kwargs)


class PaymentExportMixin:
    """支付数据导出混入类"""
    
    def export_csv(self, queryset, filename_prefix):
        """导出CSV格式"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        self.write_csv_headers(writer)
        
        for item in queryset:
            self.write_csv_row(writer, item)
        
        return response
    
    def export_excel(self, queryset, filename_prefix):
        """导出Excel格式"""
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # 写入表头
        headers = self.get_excel_headers()
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # 写入数据
        for row, item in enumerate(queryset, start=1):
            self.write_excel_row(worksheet, row, item)
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
        
        return response
    
    def get_excel_headers(self):
        """获取Excel表头"""
        raise NotImplementedError
    
    def write_excel_row(self, worksheet, row, item):
        """写入Excel行数据"""
        raise NotImplementedError
    
    def write_csv_headers(self, writer):
        """写入CSV表头"""
        raise NotImplementedError
    
    def write_csv_row(self, writer, item):
        """写入CSV行数据"""
        raise NotImplementedError


class PaymentExportView(LoginRequiredMixin, UserPassesTestMixin, PaymentExportMixin, View):
    """支付记录导出视图"""
    template_name = 'games/admin/payment_export.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = MembershipPayment.objects.all().order_by('-created_at')
        
        # 应用过滤条件
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status = self.request.GET.get('status')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_excel_headers(self):
        return [
            _('ID'), _('User'), _('Membership'), _('Amount'),
            _('Currency'), _('Status'), _('Created At'),
            _('Transaction ID'), _('Payment Method')
        ]
    
    def write_excel_row(self, worksheet, row, payment):
        worksheet.write(row, 0, payment.id)
        worksheet.write(row, 1, payment.user.username)
        worksheet.write(row, 2, payment.membership.name if payment.membership else '')
        worksheet.write(row, 3, float(payment.total))
        worksheet.write(row, 4, payment.currency)
        worksheet.write(row, 5, payment.get_status_display())
        worksheet.write(row, 6, payment.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        worksheet.write(row, 7, payment.transaction_id or '')
        worksheet.write(row, 8, payment.payment_method_code)
    
    def write_csv_headers(self, writer):
        writer.writerow(self.get_excel_headers())
    
    def write_csv_row(self, writer, payment):
        writer.writerow([
            payment.id,
            payment.user.username,
            payment.membership.name if payment.membership else '',
            payment.total,
            payment.currency,
            payment.get_status_display(),
            payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            payment.transaction_id or '',
            payment.payment_method_code
        ])
    
    def get(self, request, *args, **kwargs):
        format_type = request.GET.get('format', 'csv')
        queryset = self.get_queryset()
        
        if format_type == 'excel':
            return self.export_excel(queryset, 'payments')
        else:
            return self.export_csv(queryset, 'payments')


class PaymentStatisticsExportView(LoginRequiredMixin, UserPassesTestMixin, PaymentExportMixin, View):
    """支付统计导出视图"""
    template_name = 'games/admin/payment_statistics_export.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = PaymentStatistics.objects.all().order_by('-date')
        
        # 应用过滤条件
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    def get_excel_headers(self):
        return [
            _('Date'), _('Total Payments'), _('Successful Payments'),
            _('Failed Payments'), _('Total Amount'), _('Successful Amount'),
            _('New Members'), _('Renewals'), _('Conversion Rate')
        ]
    
    def write_excel_row(self, worksheet, row, stat):
        worksheet.write(row, 0, stat.date.strftime('%Y-%m-%d'))
        worksheet.write(row, 1, stat.total_payments)
        worksheet.write(row, 2, stat.successful_payments)
        worksheet.write(row, 3, stat.failed_payments)
        worksheet.write(row, 4, float(stat.total_amount))
        worksheet.write(row, 5, float(stat.successful_amount))
        worksheet.write(row, 6, stat.new_members)
        worksheet.write(row, 7, stat.renewals)
        worksheet.write(row, 8, f"{stat.get_conversion_rate(stat.date, stat.date):.2f}%")
    
    def write_csv_headers(self, writer):
        writer.writerow(self.get_excel_headers())
    
    def write_csv_row(self, writer, stat):
        writer.writerow([
            stat.date.strftime('%Y-%m-%d'),
            stat.total_payments,
            stat.successful_payments,
            stat.failed_payments,
            stat.total_amount,
            stat.successful_amount,
            stat.new_members,
            stat.renewals,
            f"{stat.get_conversion_rate(stat.date, stat.date):.2f}%"
        ])
    
    def get(self, request, *args, **kwargs):
        format_type = request.GET.get('format', 'csv')
        queryset = self.get_queryset()
        
        if format_type == 'excel':
            return self.export_excel(queryset, 'payment_statistics')
        else:
            return self.export_csv(queryset, 'payment_statistics')


class PaymentTemplateForm(forms.ModelForm):
    """支付模板表单"""
    class Meta:
        model = PaymentTemplate
        fields = ['name', 'code', 'template_type', 'subject', 'content', 'variables', 'status', 'description']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'template-editor'}),
            'variables': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    variables_json = forms.CharField(
        label=_('Template Variables'),
        widget=forms.Textarea(attrs={'class': 'json-editor', 'rows': 5}),
        required=False,
        help_text=_('Enter template variables in JSON format')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 初始化JSON变量
        if self.instance.pk and self.instance.variables:
            self.fields['variables_json'].initial = json.dumps(
                self.instance.variables, indent=4
            )
    
    def clean_variables_json(self):
        """验证JSON变量"""
        json_data = self.cleaned_data.get('variables_json')
        if not json_data:
            return {}
        
        try:
            return json.loads(json_data)
        except json.JSONDecodeError:
            raise forms.ValidationError(_('Please enter valid JSON format'))
    
    def clean(self):
        """表单整体验证"""
        cleaned_data = super().clean()
        
        # 将JSON变量转换为Python对象并保存
        if 'variables_json' in cleaned_data:
            cleaned_data['variables'] = cleaned_data.pop('variables_json')
        
        return cleaned_data


@method_decorator(user_passes_test(is_admin), name='dispatch')
class PaymentTemplateListView(ListView):
    """支付模板列表视图"""
    model = PaymentTemplate
    template_name = 'games/admin/payment_template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PaymentTemplate.objects.all()
        
        # 搜索过滤
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | 
                Q(code__icontains=q) | 
                Q(description__icontains=q)
            )
        
        # 类型过滤
        template_type = self.request.GET.get('type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
            
        # 状态过滤
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 添加模板类型统计
        context['email_count'] = PaymentTemplate.objects.filter(template_type='email').count()
        context['webhook_count'] = PaymentTemplate.objects.filter(template_type='webhook').count()
        context['sms_count'] = PaymentTemplate.objects.filter(template_type='sms').count()
        
        # 添加状态统计
        context['active_count'] = PaymentTemplate.objects.filter(status='active').count()
        context['inactive_count'] = PaymentTemplate.objects.filter(status='inactive').count()
        
        return context


@method_decorator(user_passes_test(is_admin), name='dispatch')
class PaymentTemplateCreateView(CreateView):
    """创建支付模板视图"""
    model = PaymentTemplate
    form_class = PaymentTemplateForm
    template_name = 'games/admin/payment_template_form.html'
    success_url = reverse_lazy('games:admin_payment_template_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Payment Template')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Payment template has been created successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class PaymentTemplateUpdateView(UpdateView):
    """编辑支付模板视图"""
    model = PaymentTemplate
    form_class = PaymentTemplateForm
    template_name = 'games/admin/payment_template_form.html'
    success_url = reverse_lazy('games:admin_payment_template_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Payment Template')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Payment template has been updated successfully.'))
        return super().form_valid(form)


@method_decorator(user_passes_test(is_admin), name='dispatch')
class PaymentTemplateDeleteView(DeleteView):
    """删除支付模板视图"""
    model = PaymentTemplate
    template_name = 'games/admin/payment_template_confirm_delete.html'
    success_url = reverse_lazy('games:admin_payment_template_list')
    context_object_name = 'template'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Payment template has been deleted successfully.'))
        return super().delete(request, *args, **kwargs)


@login_required
@user_passes_test(is_admin)
def admin_payment_template_preview(request, template_id):
    """预览支付模板"""
    template = get_object_or_404(PaymentTemplate, id=template_id)
    
    # 准备预览数据
    preview_data = {
        'payment': {
            'id': 1,
            'user': {'username': 'test_user'},
            'membership': {'name': 'Premium Membership'},
            'total': '99.99',
            'currency': 'USD',
            'transaction_id': 'TXN123456',
            'created_at': timezone.now(),
            'failure_reason': 'Payment declined by bank'
        }
    }
    
    # 渲染模板
    subject = template.render_subject(preview_data)
    content = template.render_content(preview_data)
    
    return render(request, 'games/admin/payment_template_preview.html', {
        'template': template,
        'preview_subject': subject,
        'preview_content': content,
        'preview_data': preview_data
    })


@login_required
@user_passes_test(is_admin)
def admin_payment_template_duplicate(request, template_id):
    """复制支付模板"""
    template = get_object_or_404(PaymentTemplate, id=template_id)
    
    # 创建新模板
    new_template = PaymentTemplate.objects.create(
        name=f"{template.name} (Copy)",
        code=f"{template.code}_copy",
        template_type=template.template_type,
        subject=template.subject,
        content=template.content,
        variables=template.variables,
        status='inactive',
        description=template.description
    )
    
    messages.success(request, _('Payment template has been duplicated successfully.'))
    return redirect('games:admin_payment_template_edit', pk=new_template.pk)


@login_required
@user_passes_test(is_admin)
def admin_payment_template_toggle_status(request, template_id):
    """切换支付模板状态"""
    template = get_object_or_404(PaymentTemplate, id=template_id)
    
    # 切换状态
    template.status = 'inactive' if template.status == 'active' else 'active'
    template.save()
    
    status_text = _('activated') if template.status == 'active' else _('deactivated')
    messages.success(request, _('Payment template has been {} successfully.').format(status_text))
    return redirect('games:admin_payment_template_list')


@login_required
@user_passes_test(is_admin)
def admin_payment_template_restore_defaults(request):
    """恢复默认模板"""
    if request.method == 'POST':
        default_templates = PaymentTemplate.get_default_templates()
        
        for code, template_data in default_templates.items():
            PaymentTemplate.objects.update_or_create(
                code=code,
                defaults={
                    'name': template_data['name'],
                    'template_type': template_data['template_type'],
                    'subject': template_data['subject'],
                    'content': template_data['content'],
                    'variables': template_data['variables'],
                    'status': 'active'
                }
            )
        
        messages.success(request, _('Default payment templates have been restored successfully.'))
        return redirect('games:admin_payment_template_list')
    
    return render(request, 'games/admin/payment_template_restore_confirm.html')