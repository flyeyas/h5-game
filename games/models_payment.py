from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.dispatch import Signal
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from plans.models import Plan, UserPlan
from payments.models import BasePayment
from django_countries.fields import CountryField
from ipware import get_client_ip
import hashlib
import json
import logging
from .models import Membership, UserProfile

# 设置日志记录器
logger = logging.getLogger('payment_process')

# 自定义信号
payment_status_changed = Signal()  # 提供 sender, instance, old_status, new_status 参数


class PaymentMethod(models.Model):
    """支付方式配置模型"""
    PROVIDER_CHOICES = [
        ('payments.dummy.DummyProvider', _('Dummy Provider (Testing)')),
        ('payments.paypal.PaypalProvider', _('PayPal')),
        ('payments.stripe.StripeProvider', _('Stripe')),
        ('payments.manual.ManualProvider', _('Manual Payment')),
        ('payments.banktransfer.BankTransferProvider', _('Bank Transfer')),
    ]
    
    name = models.CharField(_('支付方式名称'), max_length=100)
    code = models.CharField(_('支付方式代码'), max_length=50, unique=True)
    provider_class = models.CharField(_('提供商类'), max_length=255, choices=PROVIDER_CHOICES)
    is_active = models.BooleanField(_('是否启用'), default=True)
    sort_order = models.PositiveIntegerField(_('排序'), default=0)
    icon = models.FileField(_('图标'), upload_to='payment_icons/', null=True, blank=True)
    description = models.TextField(_('描述'), blank=True)
    configuration = models.JSONField(_('配置参数'), default=dict, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('支付方式')
        verbose_name_plural = _('支付方式')
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_provider_instance(self, payment=None):
        """获取支付提供商实例"""
        try:
            # 解析提供商类路径
            parts = self.provider_class.split('.')
            module_path, class_name = '.'.join(parts[:-1]), parts[-1]
            
            # 动态导入
            module = __import__(module_path, fromlist=[class_name])
            provider_class = getattr(module, class_name)
            
            # 创建实例
            if payment:
                provider = provider_class(payment=payment, **self.configuration)
            else:
                provider = provider_class(**self.configuration)
                
            # 添加提供商配置作为属性，便于访问
            provider.provider_settings = self.configuration
            
            return provider
        except (ImportError, AttributeError) as e:
            logger.error(f"Error creating provider instance: {str(e)}", exc_info=True)
            return None
    
    def validate_configuration(self):
        """验证配置是否正确"""
        required_fields = {
            'payments.paypal.PaypalProvider': ['client_id', 'secret'],
            'payments.stripe.StripeProvider': ['api_key', 'public_key'],
        }
        
        if self.provider_class in required_fields:
            for field in required_fields[self.provider_class]:
                if field not in self.configuration or not self.configuration[field]:
                    return False, f"Missing required field: {field}"
        
        return True, "Configuration is valid"

    @staticmethod
    def get_payment_host():
        """获取支付主机配置"""
        try:
            from django.core.cache import cache
            host = cache.get('payment_host')
            if host is None:
                global_config = PaymentMethod.get_global_config()
                host = global_config.get('payment_host', 'localhost:8000')
                cache.set('payment_host', host, 3600)  # 缓存1小时
            return host
        except Exception as e:
            logger.error(f"Error getting payment host: {str(e)}", exc_info=True)
            return 'localhost:8000'  # 默认值

    @staticmethod
    def get_global_config():
        """获取全局支付配置，包含货币、税率、安全密钥等，优先数据库配置，后备为默认值。"""
        defaults = {
            'currency': 'USD',
            'tax': 0,
            'security_key': 'default-key-replace-in-database',
            'security_salt': 'default-salt-replace-in-database',
            'fraud_threshold': 3,
            'payment_host': 'localhost:8000',  # 添加支付主机配置
        }
        try:
            global_config = PaymentMethod.objects.filter(code='global_config').first()
            if global_config and isinstance(global_config.configuration, dict):
                config = {**defaults, **global_config.configuration}
                # 兼容旧字段
                config['currency'] = config.get('currency', defaults['currency'])
                config['tax'] = config.get('tax', defaults['tax'])
                config['security_key'] = config.get('security_key', defaults['security_key'])
                config['security_salt'] = config.get('security_salt', defaults['security_salt'])
                config['fraud_threshold'] = config.get('fraud_threshold', defaults['fraud_threshold'])
                config['payment_host'] = config.get('payment_host', defaults['payment_host'])
                return config
        except Exception as e:
            logger.error(f"Error loading global payment config: {str(e)}", exc_info=True)
        return defaults


class MembershipPlan(models.Model):
    """将Membership与django_plans的Plan关联的模型"""
    membership = models.OneToOneField(Membership, verbose_name=_('会员等级'), on_delete=models.CASCADE, related_name='plan')
    plan = models.OneToOneField(Plan, verbose_name=_('订阅计划'), on_delete=models.CASCADE, related_name='membership_plan')
    
    class Meta:
        verbose_name = _('会员订阅计划')
        verbose_name_plural = _('会员订阅计划')
    
    def __str__(self):
        return f"{self.membership.name} - {self.plan.name}"


class PaymentNotification(models.Model):
    """支付通知记录"""
    NOTIFICATION_TYPES = (
        ('email', _('Email')),
        ('webhook', _('Webhook')),
        ('sms', _('SMS')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
    )
    
    payment = models.ForeignKey('MembershipPayment', verbose_name=_('支付记录'), 
                               on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(_('通知类型'), max_length=10, choices=NOTIFICATION_TYPES)
    status = models.CharField(_('状态'), max_length=10, choices=STATUS_CHOICES, default='pending')
    recipient = models.CharField(_('接收者'), max_length=255)
    subject = models.CharField(_('主题'), max_length=255)
    content = models.TextField(_('内容'))
    sent_at = models.DateTimeField(_('发送时间'), null=True, blank=True)
    error_message = models.TextField(_('错误信息'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('支付通知')
        verbose_name_plural = _('支付通知')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.payment.id} - {self.status}"
    
    def send(self):
        """发送通知"""
        try:
            if self.notification_type == 'email':
                self._send_email()
            elif self.notification_type == 'webhook':
                self._send_webhook()
            elif self.notification_type == 'sms':
                self._send_sms()
            
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.save()
            return True
        except Exception as e:
            self.status = 'failed'
            self.error_message = str(e)
            self.save()
            logger.error(f"Failed to send payment notification: {str(e)}", exc_info=True)
            return False
    
    def _send_email(self):
        """发送邮件通知"""
        html_message = render_to_string('games/email/payment_notification.html', {
            'payment': self.payment,
            'content': self.content,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=self.subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.recipient],
            html_message=html_message,
            fail_silently=False,
        )
    
    def _send_webhook(self):
        """发送Webhook通知"""
        # 实现webhook通知逻辑
        pass
    
    def _send_sms(self):
        """发送短信通知"""
        # 实现短信通知逻辑
        pass


class PaymentStatistics(models.Model):
    """支付统计数据"""
    date = models.DateField(_('日期'), unique=True)
    total_payments = models.PositiveIntegerField(_('总支付数'), default=0)
    successful_payments = models.PositiveIntegerField(_('成功支付数'), default=0)
    failed_payments = models.PositiveIntegerField(_('失败支付数'), default=0)
    total_amount = models.DecimalField(_('总金额'), max_digits=10, decimal_places=2, default=0)
    successful_amount = models.DecimalField(_('成功金额'), max_digits=10, decimal_places=2, default=0)
    new_members = models.PositiveIntegerField(_('新会员数'), default=0)
    renewals = models.PositiveIntegerField(_('续费数'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('支付统计')
        verbose_name_plural = _('支付统计')
        ordering = ['-date']
    
    def __str__(self):
        return f"Payment Statistics - {self.date}"
    
    @classmethod
    def update_statistics(cls, payment):
        """更新支付统计数据"""
        today = timezone.now().date()
        stats, created = cls.objects.get_or_create(date=today)
        
        # 更新总支付数
        stats.total_payments += 1
        stats.total_amount += payment.total
        
        # 根据支付状态更新统计数据
        if payment.status == 'confirmed':
            stats.successful_payments += 1
            stats.successful_amount += payment.total
            
            # 检查是否为新会员或续费
            if payment.is_recurring:
                stats.renewals += 1
            else:
                # 检查用户是否为新会员
                user_payments = MembershipPayment.objects.filter(
                    user=payment.user,
                    status='confirmed',
                    created_at__lt=payment.created_at
                ).exists()
                if not user_payments:
                    stats.new_members += 1
        elif payment.status == 'rejected':
            stats.failed_payments += 1
        
        stats.save()
        return stats
    
    @classmethod
    def get_conversion_rate(cls, start_date=None, end_date=None):
        """计算会员转化率"""
        if not start_date:
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        stats = cls.objects.filter(date__range=[start_date, end_date])
        if not stats.exists():
            return 0
        
        total_visitors = User.objects.filter(
            date_joined__range=[start_date, end_date]
        ).count()
        
        if total_visitors == 0:
            return 0
        
        total_new_members = stats.aggregate(
            total=models.Sum('new_members')
        )['total'] or 0
        
        return (total_new_members / total_visitors) * 100


class MembershipPayment(BasePayment):
    """会员支付记录模型"""
    FRAUD_STATUS_CHOICES = (
        ('unknown', _('未知')),
        ('accepted', _('通过')),
        ('rejected', _('拒绝')),
        ('review', _('人工审核')),
    )
    
    user = models.ForeignKey(User, verbose_name=_('用户'), on_delete=models.CASCADE, related_name='membership_payments')
    membership = models.ForeignKey(Membership, verbose_name=_('会员等级'), on_delete=models.SET_NULL, null=True, related_name='payments')
    user_plan = models.ForeignKey(UserPlan, verbose_name=_('用户计划'), on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    transaction_id = models.CharField(_('交易ID'), max_length=255, blank=True, null=True)
    is_recurring = models.BooleanField(_('是否为续费'), default=False)
    
    # 新增安全相关字段
    payment_method_code = models.CharField(_('支付方式代码'), max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(_('IP地址'), blank=True, null=True)
    user_agent = models.TextField(_('用户代理'), blank=True)
    security_hash = models.CharField(_('安全哈希'), max_length=64, blank=True)
    fraud_status = models.CharField(_('欺诈状态'), max_length=10, choices=FRAUD_STATUS_CHOICES, default='unknown')
    fraud_details = models.JSONField(_('欺诈检测详情'), blank=True, default=dict)
    
    # 新增发票相关字段
    billing_address = models.TextField(_('账单地址'), blank=True)
    billing_country = CountryField(_('账单国家'), blank=True, null=True)
    billing_city = models.CharField(_('账单城市'), max_length=100, blank=True)
    billing_postcode = models.CharField(_('邮政编码'), max_length=20, blank=True)
    billing_company = models.CharField(_('公司名称'), max_length=100, blank=True)
    tax_id = models.CharField(_('税号'), max_length=50, blank=True)
    
    # 处理相关字段
    payment_processor_response = models.JSONField(_('支付处理器响应'), blank=True, default=dict)
    failure_reason = models.TextField(_('失败原因'), blank=True)
    retry_count = models.PositiveSmallIntegerField(_('重试次数'), default=0)
    success_at = models.DateTimeField(_('支付成功时间'), null=True, blank=True)
    
    # 添加超时相关字段
    timeout_at = models.DateTimeField(_('超时时间'), null=True, blank=True)
    timeout_notification_sent = models.BooleanField(_('已发送超时通知'), default=False)
    
    class Meta:
        verbose_name = _('会员支付记录')
        verbose_name_plural = _('会员支付记录')
        ordering = ['-created_at']
    
    def get_absolute_url(self):
        return reverse('games:payment_method_selection', kwargs={'payment_id': self.id})
    
    def get_failure_url(self):
        return reverse('games:payment_failed', kwargs={'payment_id': self.pk})
    
    def get_success_url(self):
        return reverse('games:payment_success', kwargs={'payment_id': self.pk})
    
    def get_process_url(self):
        return reverse('games:payment_process', kwargs={'payment_id': self.pk})
    
    def get_purchased_items(self):
        from payments.models import PurchasedItem
        return [
            PurchasedItem(
                name=self.membership.name,
                sku=f"membership-{self.membership.id}",
                quantity=1,
                price=self.membership.price,
                currency=self.currency
            )
        ]
    
    def generate_security_hash(self):
        """生成安全哈希"""
        data = {
            'payment_id': str(self.id),
            'user_id': str(self.user.id),
            'amount': str(self.total),
            'currency': self.currency,
            'created_at': str(self.created_at.timestamp())
        }
        json_data = json.dumps(data, sort_keys=True)
        # 尝试从数据库获取安全配置
        try:
            from django.core.cache import cache
            security_key = cache.get('payment_security_key')
            security_salt = cache.get('payment_security_salt')
            if not security_key or not security_salt:
                global_config = PaymentMethod.get_global_config()
                security_key = global_config['security_key']
                security_salt = global_config['security_salt']
                cache.set('payment_security_key', security_key, 3600)
                cache.set('payment_security_salt', security_salt, 3600)
        except:
            global_config = PaymentMethod.get_global_config()
            security_key = global_config['security_key']
            security_salt = global_config['security_salt']
        hash_obj = hashlib.sha256((json_data + security_key + security_salt).encode())
        return hash_obj.hexdigest()
    
    def verify_security_hash(self, provided_hash=None):
        """验证安全哈希"""
        if provided_hash is None:
            provided_hash = self.security_hash
        
        expected_hash = self.generate_security_hash()
        return provided_hash == expected_hash
    
    def record_ip_info(self, request):
        """记录IP和用户代理信息"""
        if request:
            client_ip, is_routable = get_client_ip(request)
            if client_ip:
                self.ip_address = client_ip
            
            self.user_agent = request.META.get('HTTP_USER_AGENT', '')
            self.save(update_fields=['ip_address', 'user_agent'])
    
    def check_fraud(self, request=None):
        """检查欺诈风险"""
        risk_score = 0
        fraud_details = {}
        try:
            from django.core.cache import cache
            fraud_threshold = cache.get('payment_fraud_threshold')
            if fraud_threshold is None:
                global_config = PaymentMethod.get_global_config()
                fraud_threshold = global_config['fraud_threshold']
                cache.set('payment_fraud_threshold', fraud_threshold, 3600)
        except:
            global_config = PaymentMethod.get_global_config()
            fraud_threshold = global_config['fraud_threshold']
        
        # 检查IP地址
        if self.ip_address:
            # 这里可以添加IP地址检查逻辑，例如检查是否为高风险国家等
            pass
        
        # 检查支付尝试次数
        attempts = PaymentAttempt.objects.filter(
            user=self.user, 
            created_at__gte=timezone.now() - timezone.timedelta(hours=24),
            status='failed'
        ).count()
        
        if attempts >= fraud_threshold:
            risk_score += 50
            fraud_details['high_failure_rate'] = True
        
        # 用户账户年龄检查
        account_age_days = (timezone.now() - self.user.date_joined).days
        if account_age_days < 7:
            risk_score += 20
            fraud_details['new_account'] = True
        
        # 根据风险分数设置欺诈状态
        if risk_score >= 70:
            self.fraud_status = 'rejected'
        elif risk_score >= 40:
            self.fraud_status = 'review'
        else:
            self.fraud_status = 'accepted'
        
        self.fraud_details = fraud_details
        self.save(update_fields=['fraud_status', 'fraud_details'])
        
        # 记录高风险交易
        if self.fraud_status in ['rejected', 'review']:
            logger.warning(
                f"High risk payment detected: ID={self.id}, "
                f"User={self.user.username}, Risk Score={risk_score}, "
                f"Status={self.fraud_status}, Details={fraud_details}"
            )
        
        return self.fraud_status
        
    def send_payment_notification(self, notification_type='email', status=None):
        """发送支付状态通知"""
        if status is None:
            status = self.status
        
        # 获取对应的模板代码
        template_code = None
        if status == 'confirmed':
            template_code = 'payment_confirmed'
        elif status == 'rejected':
            template_code = 'payment_rejected'
        elif status == 'timeout':
            template_code = 'payment_timeout'
        
        # 获取模板
        template = PaymentTemplate.get_template(template_code, notification_type)
        
        if template:
            # 准备模板上下文
            context = {
                'payment': self,
                'user': self.user,
                'membership': self.membership
            }
            
            # 渲染模板内容
            subject = template.render_subject(context)
            content = template.render_content(context)
        else:
            # 如果没有找到模板，使用默认内容
            if status == 'confirmed':
                subject = _('Payment Successful - {}').format(self.membership.name)
                content = _('Your payment of {} {} for {} membership has been confirmed.').format(
                    self.total, self.currency, self.membership.name
                )
            elif status == 'rejected':
                subject = _('Payment Failed - {}').format(self.membership.name)
                content = _('Your payment of {} {} for {} membership has failed. Reason: {}').format(
                    self.total, self.currency, self.membership.name, self.failure_reason
                )
            else:
                subject = _('Payment Status Update - {}').format(self.membership.name)
                content = _('Your payment status has been updated to: {}').format(status)
        
        # 创建通知记录
        notification = PaymentNotification.objects.create(
            payment=self,
            notification_type=notification_type,
            recipient=self.billing_email,
            subject=subject,
            content=content
        )
        
        # 使用异步任务发送通知
        from .tasks import send_payment_notification
        send_payment_notification.delay(notification.id)
        
        return notification
    
    def set_timeout(self, timeout_minutes=30):
        """设置支付超时时间"""
        self.timeout_at = timezone.now() + timezone.timedelta(minutes=timeout_minutes)
        self.save(update_fields=['timeout_at'])
    
    def check_timeout(self):
        """检查支付是否超时"""
        if not self.timeout_at or self.status in ['confirmed', 'rejected']:
            return False
            
        if timezone.now() > self.timeout_at:
            # 更新支付状态
            self.status = 'rejected'
            self.failure_reason = _('Payment timeout')
            self.save(update_fields=['status', 'failure_reason'])
            
            # 发送超时通知
            if not self.timeout_notification_sent:
                self.send_payment_notification(
                    notification_type='email',
                    status='rejected'
                )
                self.timeout_notification_sent = True
                self.save(update_fields=['timeout_notification_sent'])
            
            # 记录日志
            logger.warning(
                f"Payment timeout: ID={self.id}, "
                f"User={self.user.username}, "
                f"Timeout At={self.timeout_at}"
            )
            
            return True
        
        return False
    
    def save(self, *args, **kwargs):
        # 如果是新创建的支付记录，设置超时时间
        if not self.pk:
            super().save(*args, **kwargs)
            self.set_timeout()
            return super().save(update_fields=['timeout_at'])
        
        # 保存前检查状态变化
        if self.pk:
            try:
                old_status = MembershipPayment.objects.get(pk=self.pk).status
                super().save(*args, **kwargs)
                # 如果状态发生变化，触发信号和通知
                if old_status != self.status:
                    # 如果支付成功，记录成功时间
                    if self.status == 'confirmed' and not self.success_at:
                        self.success_at = timezone.now()
                        self.save(update_fields=['success_at'])
                    
                    # 更新支付统计
                    PaymentStatistics.update_statistics(self)
                    
                    # 发送状态变更通知
                    self.send_payment_notification()
                    
                    # 触发信号
                    payment_status_changed.send(
                        sender=self.__class__, 
                        instance=self, 
                        old_status=old_status, 
                        new_status=self.status
                    )
                    
                    # 记录状态变化日志
                    logger.info(
                        f"Payment status changed: ID={self.id}, "
                        f"User={self.user.username}, "
                        f"Old Status={old_status}, New Status={self.status}"
                    )
            except MembershipPayment.DoesNotExist:
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    def payment_success(self):
        """支付成功后的处理"""
        # 获取用户资料
        try:
            profile = self.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=self.user)
        
        # 设置会员等级和到期时间
        profile.membership = self.membership
        
        # 如果已经有会员，则延长时间，否则从当前时间开始计算
        if profile.membership_expiry and profile.membership_expiry > timezone.now():
            profile.membership_expiry += timezone.timedelta(days=self.membership.duration_days)
        else:
            profile.membership_expiry = timezone.now() + timezone.timedelta(days=self.membership.duration_days)
        
        profile.save()
        
        # 更新用户计划状态
        if self.user_plan:
            self.user_plan.active = True
            self.user_plan.expire = profile.membership_expiry
            self.user_plan.save()
        
        # 成功时间
        self.success_at = timezone.now()    
            
        # 记录交易ID
        if not self.transaction_id and hasattr(self, 'transaction_id'):
            self.transaction_id = f"txn_{self.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            self.save(update_fields=['transaction_id', 'success_at'])
        
        # 创建发票
        PaymentInvoice.objects.create(
            payment=self,
            invoice_number=f"INV-{self.id}-{timezone.now().strftime('%Y%m%d')}",
            invoice_date=timezone.now()
        )
            
        # 记录成功日志
        logger.info(
            f"Payment successful: ID={self.id}, "
            f"User={self.user.username}, "
            f"Amount={self.total} {self.currency}, "
            f"Membership={self.membership.name if self.membership else 'Unknown'}"
        )
        
        return True


class PaymentAttempt(models.Model):
    """支付尝试记录，用于跟踪每次支付尝试"""
    STATUS_CHOICES = (
        ('pending', _('处理中')),
        ('success', _('成功')),
        ('failed', _('失败')),
    )
    
    payment = models.ForeignKey(MembershipPayment, verbose_name=_('支付记录'), 
                               on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, verbose_name=_('用户'), 
                           on_delete=models.CASCADE, related_name='payment_attempts')
    payment_method_code = models.CharField(_('支付方式代码'), max_length=50)
    status = models.CharField(_('状态'), max_length=10, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField(_('IP地址'), blank=True, null=True)
    user_agent = models.TextField(_('用户代理'), blank=True)
    error_message = models.TextField(_('错误信息'), blank=True)
    provider_reference = models.CharField(_('提供商参考号'), max_length=255, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('支付尝试')
        verbose_name_plural = _('支付尝试')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.payment_method_code} - {self.status}"
    
    @classmethod
    def record_attempt(cls, payment, request=None, method_code=None, status='pending'):
        """记录支付尝试"""
        attempt = cls(
            payment=payment,
            user=payment.user,
            payment_method_code=method_code or payment.payment_method_code,
            status=status
        )
        
        if request:
            client_ip, is_routable = get_client_ip(request)
            if client_ip:
                attempt.ip_address = client_ip
            
            attempt.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        attempt.save()
        return attempt


class PaymentInvoice(models.Model):
    """支付发票模型"""
    payment = models.OneToOneField(MembershipPayment, verbose_name=_('支付记录'), 
                                  on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(_('发票号'), max_length=50, unique=True)
    invoice_date = models.DateTimeField(_('发票日期'))
    pdf_file = models.FileField(_('PDF文件'), upload_to='invoices/', null=True, blank=True)
    sent_to_email = models.BooleanField(_('已发送邮件'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('支付发票')
        verbose_name_plural = _('支付发票')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.invoice_number
    
    def get_absolute_url(self):
        return reverse('games:payment_invoice_detail', kwargs={'invoice_id': self.pk})


class PaymentTemplate(models.Model):
    """支付模板模型"""
    TEMPLATE_TYPES = (
        ('email', _('Email Template')),
        ('webhook', _('Webhook Template')),
        ('sms', _('SMS Template')),
    )
    
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('inactive', _('Inactive')),
    )
    
    name = models.CharField(_('Template Name'), max_length=100)
    code = models.CharField(_('Template Code'), max_length=50, unique=True)
    template_type = models.CharField(_('Template Type'), max_length=10, choices=TEMPLATE_TYPES)
    subject = models.CharField(_('Subject'), max_length=255, blank=True)
    content = models.TextField(_('Content'))
    variables = models.JSONField(_('Template Variables'), default=dict, help_text=_('Available template variables'))
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='active')
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Payment Template')
        verbose_name_plural = _('Payment Templates')
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.get_template_type_display()} - {self.name}"
    
    def render_content(self, context):
        """渲染模板内容"""
        from django.template import Template, Context
        try:
            template = Template(self.content)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Error rendering payment template: {str(e)}", exc_info=True)
            return self.content
    
    def render_subject(self, context):
        """渲染模板主题"""
        from django.template import Template, Context
        try:
            template = Template(self.subject)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Error rendering payment template subject: {str(e)}", exc_info=True)
            return self.subject
    
    @classmethod
    def get_template(cls, code, template_type='email'):
        """获取指定代码和类型的模板"""
        try:
            return cls.objects.get(code=code, template_type=template_type, status='active')
        except cls.DoesNotExist:
            logger.warning(f"Payment template not found: code={code}, type={template_type}")
            return None
    
    @classmethod
    def get_default_templates(cls):
        """获取默认模板配置"""
        return {
            'payment_confirmed': {
                'name': _('Payment Confirmation'),
                'code': 'payment_confirmed',
                'template_type': 'email',
                'subject': _('Payment Successful - {{ payment.membership.name }}'),
                'content': _('''
                    <h2>Payment Successful</h2>
                    <p>Dear {{ payment.user.username }},</p>
                    <p>Your payment of {{ payment.total }} {{ payment.currency }} for {{ payment.membership.name }} membership has been confirmed.</p>
                    <p>Transaction ID: {{ payment.transaction_id }}</p>
                    <p>Payment Date: {{ payment.created_at|date:"Y-m-d H:i:s" }}</p>
                    <p>Thank you for your subscription!</p>
                '''),
                'variables': {
                    'payment': 'Payment object',
                    'user': 'User object',
                    'membership': 'Membership object'
                }
            },
            'payment_rejected': {
                'name': _('Payment Rejection'),
                'code': 'payment_rejected',
                'template_type': 'email',
                'subject': _('Payment Failed - {{ payment.membership.name }}'),
                'content': _('''
                    <h2>Payment Failed</h2>
                    <p>Dear {{ payment.user.username }},</p>
                    <p>Your payment of {{ payment.total }} {{ payment.currency }} for {{ payment.membership.name }} membership has failed.</p>
                    <p>Reason: {{ payment.failure_reason }}</p>
                    <p>Please try again or contact our support team for assistance.</p>
                '''),
                'variables': {
                    'payment': 'Payment object',
                    'user': 'User object',
                    'membership': 'Membership object'
                }
            },
            'payment_timeout': {
                'name': _('Payment Timeout'),
                'code': 'payment_timeout',
                'template_type': 'email',
                'subject': _('Payment Timeout - {{ payment.membership.name }}'),
                'content': _('''
                    <h2>Payment Timeout</h2>
                    <p>Dear {{ payment.user.username }},</p>
                    <p>Your payment of {{ payment.total }} {{ payment.currency }} for {{ payment.membership.name }} membership has timed out.</p>
                    <p>Please try again to complete your subscription.</p>
                '''),
                'variables': {
                    'payment': 'Payment object',
                    'user': 'User object',
                    'membership': 'Membership object'
                }
            }
        }