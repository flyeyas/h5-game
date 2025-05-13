from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from core.models import PaymentGateway, SubscriptionPlan, Subscription, PaymentTransaction


class StaffRequiredMixin(UserPassesTestMixin):
    """确保只有管理员才能访问视图"""
    def test_func(self):
        return self.request.user.is_staff


# 支付网关管理视图
class PaymentGatewayListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = PaymentGateway
    template_name = 'admin/payments/gateway_list.html'
    context_object_name = 'gateways'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('支付网关管理')
        
        # 添加统计数据
        gateways = context['gateways']
        context['active_gateways'] = sum(1 for g in gateways if g.is_active)
        context['default_gateways'] = sum(1 for g in gateways if g.is_default)
        context['test_mode_gateways'] = sum(1 for g in gateways if g.test_mode)
        
        return context


class PaymentGatewayCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = PaymentGateway
    template_name = 'admin/payments/gateway_form.html'
    fields = ['name', 'gateway_type', 'is_active', 'is_default', 'test_mode', 
              'display_order', 'success_url', 'cancel_url']
    success_url = reverse_lazy('admin_panel:payment_gateway_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('添加支付网关')
        context['is_add'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('支付网关添加成功'))
        return response


class PaymentGatewayUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = PaymentGateway
    template_name = 'admin/payments/gateway_form.html'
    fields = ['name', 'gateway_type', 'is_active', 'is_default', 'test_mode', 
              'display_order', 'success_url', 'cancel_url']
    success_url = reverse_lazy('admin_panel:payment_gateway_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('编辑支付网关')
        context['is_edit'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('支付网关更新成功'))
        return response


class PaymentGatewayDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = PaymentGateway
    template_name = 'admin/payments/gateway_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:payment_gateway_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('删除支付网关')
        return context
    
    def delete(self, request, *args, **kwargs):
        gateway = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _(f'支付网关 "{gateway.name}" 已成功删除'))
        return response


class PaymentGatewayConfigView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = PaymentGateway
    template_name = 'admin/payments/gateway_config.html'
    fields = ['config']
    success_url = reverse_lazy('admin_panel:payment_gateway_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('配置支付网关')
        context['gateway_type'] = self.object.get_gateway_type_display()
        
        # 根据不同网关类型提供不同的配置字段和说明
        config_fields = self.get_config_fields(self.object.gateway_type)
        context['config_fields'] = config_fields
        return context
    
    def get_config_fields(self, gateway_type):
        """根据网关类型返回配置字段"""
        fields = {}
        
        # PayPal配置字段
        if gateway_type == 'paypal':
            fields = {
                'environment': {
                    'label': _('环境'),
                    'type': 'select',
                    'options': [('sandbox', _('沙盒环境')), ('production', _('生产环境'))],
                    'default': 'sandbox',
                    'help_text': _('选择PayPal API环境'),
                },
                'client_id': {
                    'label': _('Client ID'),
                    'type': 'text',
                    'default': '',
                    'help_text': _('PayPal开发者平台获取的Client ID'),
                },
                'secret_key': {
                    'label': _('Secret Key'),
                    'type': 'password',
                    'default': '',
                    'help_text': _('PayPal开发者平台获取的Secret Key'),
                },
                'currency': {
                    'label': _('默认货币'),
                    'type': 'text',
                    'default': 'USD',
                    'help_text': _('默认支付货币代码，例如USD、EUR等'),
                },
                'locale': {
                    'label': _('语言设置'),
                    'type': 'text',
                    'default': 'zh_CN',
                    'help_text': _('PayPal界面语言代码'),
                },
                'ipn_url': {
                    'label': _('IPN通知URL'),
                    'type': 'text',
                    'default': '/payments/paypal/ipn/',
                    'help_text': _('接收PayPal付款通知的URL'),
                }
            }
        # 支付宝配置字段
        elif gateway_type == 'alipay':
            fields = {
                'app_id': {
                    'label': _('应用ID (App ID)'),
                    'type': 'text',
                    'default': '',
                    'help_text': _('支付宝开放平台申请的应用ID'),
                },
                'app_private_key': {
                    'label': _('应用私钥 (App Private Key)'),
                    'type': 'textarea',
                    'default': '',
                    'help_text': _('PKCS1或PKCS8格式RSA2私钥'),
                },
                'alipay_public_key': {
                    'label': _('支付宝公钥 (Alipay Public Key)'),
                    'type': 'textarea',
                    'default': '',
                    'help_text': _('支付宝提供的公钥'),
                },
                'sign_type': {
                    'label': _('签名方式'),
                    'type': 'select',
                    'options': [('RSA2', 'RSA2'), ('RSA', 'RSA')],
                    'default': 'RSA2',
                    'help_text': _('推荐使用RSA2'),
                },
                'gateway_url': {
                    'label': _('网关地址'),
                    'type': 'select',
                    'options': [
                        ('https://openapi.alipay.com/gateway.do', _('国内版')),
                        ('https://global.alipay.com/gateway.do', _('国际版'))
                    ],
                    'default': 'https://openapi.alipay.com/gateway.do',
                    'help_text': _('支付宝网关地址'),
                },
                'notify_url': {
                    'label': _('异步通知URL'),
                    'type': 'text',
                    'default': '/payments/alipay/notify/',
                    'help_text': _('支付结果异步通知地址'),
                },
                'return_url': {
                    'label': _('同步返回URL'),
                    'type': 'text',
                    'default': '/payments/alipay/return/',
                    'help_text': _('支付成功后跳转地址'),
                },
            }
        # 微信支付配置字段
        elif gateway_type == 'wechat':
            fields = {
                'app_id': {
                    'label': _('应用ID (AppID)'),
                    'type': 'text',
                    'default': '',
                    'help_text': _('微信支付申请的应用ID'),
                },
                'mch_id': {
                    'label': _('商户ID (Mch ID)'),
                    'type': 'text',
                    'default': '',
                    'help_text': _('微信支付商户平台的商户号'),
                },
                'api_key': {
                    'label': _('API密钥 (API Key)'),
                    'type': 'password',
                    'default': '',
                    'help_text': _('微信商户平台API密钥'),
                },
                'cert_path': {
                    'label': _('证书路径 (apiclient_cert.pem)'),
                    'type': 'text',
                    'default': '',
                    'help_text': _('微信支付证书路径，用于退款等操作'),
                },
                'key_path': {
                    'label': _('密钥路径 (apiclient_key.pem)'),
                    'type': 'text',
                    'default': '',
                    'help_text': _('微信支付证书密钥路径'),
                },
                'notify_url': {
                    'label': _('通知URL'),
                    'type': 'text',
                    'default': '/payments/wechat/notify/',
                    'help_text': _('支付结果通知回调URL'),
                },
                'trade_type': {
                    'label': _('交易类型'),
                    'type': 'select',
                    'options': [
                        ('JSAPI', 'JSAPI支付(公众号)'), 
                        ('NATIVE', 'NATIVE支付(扫码)'),
                        ('APP', 'APP支付(APP)'),
                        ('MWEB', 'H5支付(H5)')
                    ],
                    'default': 'NATIVE',
                    'help_text': _('微信支付类型'),
                },
            }
        # Stripe配置字段
        elif gateway_type == 'stripe':
            fields = {
                'publishable_key': {
                    'label': _('可发布密钥 (Publishable Key)'),
                    'type': 'text',
                    'default': '',
                    'help_text': _('Stripe Dashboard获取的可发布密钥'),
                },
                'secret_key': {
                    'label': _('密钥 (Secret Key)'),
                    'type': 'password',
                    'default': '',
                    'help_text': _('Stripe Dashboard获取的密钥'),
                },
                'webhook_secret': {
                    'label': _('Webhook密钥'),
                    'type': 'password',
                    'default': '',
                    'help_text': _('用于验证Stripe发送的Webhook事件'),
                },
                'currency': {
                    'label': _('默认货币'),
                    'type': 'text',
                    'default': 'usd',
                    'help_text': _('默认支付货币代码，小写，例如usd、eur等'),
                },
                'payment_method_types': {
                    'label': _('支付方式'),
                    'type': 'text',
                    'default': 'card',
                    'help_text': _('支持的支付方式，多个用逗号分隔，例如:card,alipay'),
                },
                'webhook_url': {
                    'label': _('Webhook URL'),
                    'type': 'text',
                    'default': '/payments/stripe/webhook/',
                    'help_text': _('接收Stripe事件通知的URL'),
                },
            }
            
        return fields
    
    def form_valid(self, form):
        # 处理提交的配置
        gateway = form.instance
        config_data = {}
        
        for key, value in self.request.POST.items():
            if key.startswith('config_'):
                field_name = key.replace('config_', '')
                config_data[field_name] = value
        
        gateway.config = config_data
        response = super().form_valid(form)
        messages.success(self.request, _('支付网关配置已更新'))
        return response


class PaymentGatewayTestView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = PaymentGateway
    template_name = 'admin/payments/gateway_test.html'
    context_object_name = 'gateway'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('测试支付网关')
        return context
    
    def post(self, request, *args, **kwargs):
        gateway = self.get_object()
        amount = request.POST.get('amount', '0.01')
        
        result = self.test_gateway_connection(gateway, amount)
        
        return JsonResponse(result)
    
    def test_gateway_connection(self, gateway, amount):
        """测试支付网关连接，返回结果"""
        result = {'success': False, 'message': ''}
        
        try:
            # 根据不同网关类型进行测试
            if gateway.gateway_type == 'paypal':
                # PayPal测试逻辑
                result = self.test_paypal(gateway, amount)
            elif gateway.gateway_type == 'alipay':
                # 支付宝测试逻辑
                result = self.test_alipay(gateway, amount)
            # 其他网关类型的测试逻辑...
            else:
                result['message'] = _('暂不支持该网关类型的测试')
        except Exception as e:
            result['message'] = str(e)
        
        return result
    
    def test_paypal(self, gateway, amount):
        """测试PayPal连接"""
        result = {'success': False, 'message': ''}
        
        try:
            import requests
            
            # 获取PayPal配置
            config = gateway.config
            client_id = config.get('client_id')
            secret_key = config.get('secret_key')
            
            if not client_id or not secret_key:
                result['message'] = _('缺少PayPal Client ID或Secret Key')
                return result
            
            # 确定API endpoint
            environment = config.get('environment', 'sandbox')
            if environment == 'sandbox':
                api_base = 'https://api-m.sandbox.paypal.com'
            else:
                api_base = 'https://api-m.paypal.com'
            
            # 获取OAuth 2.0访问令牌
            auth_url = f"{api_base}/v1/oauth2/token"
            auth_response = requests.post(
                auth_url, 
                auth=(client_id, secret_key),
                data={'grant_type': 'client_credentials'},
                headers={'Accept': 'application/json', 'Accept-Language': 'en_US'}
            )
            
            if auth_response.status_code != 200:
                result['message'] = _('PayPal认证失败: ') + auth_response.text
                return result
            
            access_token = auth_response.json()['access_token']
            
            # 测试获取PayPal其他信息或创建订单
            test_url = f"{api_base}/v2/checkout/orders"
            test_response = requests.post(
                test_url,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}'
                },
                json={
                    'intent': 'CAPTURE',
                    'purchase_units': [{
                        'amount': {
                            'currency_code': config.get('currency', 'USD'),
                            'value': amount
                        }
                    }]
                }
            )
            
            if test_response.status_code in [200, 201]:
                result['success'] = True
                result['message'] = _('PayPal连接测试成功')
            else:
                result['message'] = _('PayPal API调用失败: ') + test_response.text
                
        except Exception as e:
            result['message'] = _('测试过程中发生错误: ') + str(e)
            
        return result
    
    def test_alipay(self, gateway, amount):
        """测试支付宝连接"""
        result = {'success': False, 'message': ''}
        
        try:
            # 支付宝测试逻辑
            # 这里需要根据实际使用的支付宝SDK进行集成
            result['message'] = _('支付宝测试暂未实现')
        except Exception as e:
            result['message'] = _('测试过程中发生错误: ') + str(e)
            
        return result


# 订阅计划管理视图
class SubscriptionPlanListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = SubscriptionPlan
    template_name = 'admin/payments/plan_list.html'
    context_object_name = 'plans'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('订阅计划管理')
        
        # 添加统计数据
        plans = context['plans']
        context['active_plans'] = sum(1 for p in plans if p.is_active)
        
        # 获取总订阅数
        context['total_subscriptions'] = Subscription.objects.count()
        
        # 计算总收入（假设每个订阅都有一个支付交易）
        total_revenue = 0
        try:
            from django.db.models import Sum
            total_revenue = PaymentTransaction.objects.filter(
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            # 格式化为两位小数
            context['total_revenue'] = round(float(total_revenue), 2)
        except Exception:
            context['total_revenue'] = 0
            
        return context


class SubscriptionPlanCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = SubscriptionPlan
    template_name = 'admin/payments/plan_form.html'
    fields = ['name', 'price', 'period', 'description', 'features', 'is_active']
    success_url = reverse_lazy('admin_panel:subscription_plan_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('添加订阅计划')
        context['is_add'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('订阅计划添加成功'))
        return response


class SubscriptionPlanUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = SubscriptionPlan
    template_name = 'admin/payments/plan_form.html'
    fields = ['name', 'price', 'period', 'description', 'features', 'is_active']
    success_url = reverse_lazy('admin_panel:subscription_plan_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('编辑订阅计划')
        context['is_edit'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('订阅计划更新成功'))
        return response


class SubscriptionPlanDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = SubscriptionPlan
    template_name = 'admin/payments/plan_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:subscription_plan_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('删除订阅计划')
        return context
    
    def delete(self, request, *args, **kwargs):
        plan = self.get_object()
        
        # 检查是否有活跃订阅使用此计划
        active_subs = Subscription.objects.filter(plan=plan, status__in=['active', 'trial']).count()
        if active_subs > 0:
            messages.error(request, _(f'无法删除，当前有{active_subs}个活跃订阅使用此计划'))
            return redirect('admin_panel:subscription_plan_list')
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _(f'订阅计划 "{plan.name}" 已成功删除'))
        return response


# 会员管理视图
class SubscriptionListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Subscription
    template_name = 'admin/payments/subscription_list.html'
    context_object_name = 'subscriptions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 支持过滤
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(user__username__icontains=search) | queryset.filter(user__email__icontains=search)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('会员订阅管理')
        context['status_choices'] = Subscription.STATUS_CHOICES
        
        # 添加统计数据
        context['total_subscriptions'] = Subscription.objects.count()
        context['active_subscriptions'] = Subscription.objects.filter(status='active').count()
        context['trial_subscriptions'] = Subscription.objects.filter(status='trial').count()
        context['cancelled_subscriptions'] = Subscription.objects.filter(status='cancelled').count()
        context['expired_subscriptions'] = Subscription.objects.filter(status='expired').count()
        context['auto_renew_subscriptions'] = Subscription.objects.filter(auto_renew=True).count()
        
        return context


class SubscriptionDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Subscription
    template_name = 'admin/payments/subscription_detail.html'
    context_object_name = 'subscription'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('订阅详情')
        # 获取关联的交易记录
        context['transactions'] = PaymentTransaction.objects.filter(subscription=self.object).order_by('-created_at')
        return context


class SubscriptionUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Subscription
    template_name = 'admin/payments/subscription_form.html'
    fields = ['plan', 'status', 'start_date', 'end_date', 'auto_renew']
    
    def get_success_url(self):
        return reverse('admin_panel:subscription_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('编辑订阅')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('订阅信息已更新'))
        return response 