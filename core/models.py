from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone


class GameCategory(models.Model):
    """游戏分类模型 - 前台和后台共用"""
    name = models.CharField(_("分类名称"), max_length=100)
    slug = models.SlugField(_("别名"), max_length=100, unique=True)
    description = models.TextField(_("分类描述"), blank=True)
    icon = models.CharField(_("图标类名"), max_length=50, blank=True, 
                          help_text=_("Font Awesome图标类名，例如: fas fa-gamepad"))
    color = models.CharField(_("分类颜色"), max_length=7, default="#6EBD6E", blank=True, 
                           help_text=_("用于分类标签和图标背景"))
    parent = models.ForeignKey('self', verbose_name=_("父级分类"), on_delete=models.SET_NULL, 
                              null=True, blank=True, related_name="children")
    order = models.IntegerField(_("排序"), default=0, help_text=_("数字越小排序越靠前"))
    is_active = models.BooleanField(_("是否启用"), default=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("游戏分类")
        verbose_name_plural = _("游戏分类")
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
        
    @property
    def game_count(self):
        """返回分类关联的游戏数量"""
        return self.games.count()


class GameTag(models.Model):
    """游戏标签模型 - 前台和后台共用"""
    name = models.CharField(_('标签名称'), max_length=50, db_index=True)  # 添加索引提高查询性能
    slug = models.SlugField(_("别名"), max_length=50, unique=True)
    is_active = models.BooleanField(_('是否启用'), default=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _('游戏标签')
        verbose_name_plural = _('游戏标签')
        indexes = [
            models.Index(fields=['name'], name='core_gametag_name_idx'),
            models.Index(fields=['is_active'], name='core_gametag_active_idx'),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    @property
    def game_count(self):
        """返回使用此标签的游戏数量"""
        return self.games.count()


class Game(models.Model):
    """游戏模型 - 前台和后台共用"""
    
    STATUS_CHOICES = [
        ('online', _('已上线')),
        ('offline', _('已下线')),
        ('pending', _('待审核')),
    ]
    
    title = models.CharField(_("游戏标题"), max_length=100)
    slug = models.SlugField(_("别名"), max_length=100, unique=True)
    summary = models.CharField(_("简单介绍"), max_length=200, blank=True, help_text=_("简短介绍，显示在游戏列表中"))
    description = models.TextField(_("游戏描述"))
    thumbnail = models.ImageField(_("缩略图"), upload_to="games/thumbnails/", blank=True, null=True)
    iframe_url = models.URLField(_("游戏iframe地址"), max_length=500)
    iframe_width = models.CharField(_("iframe宽度"), max_length=50, default="100%")
    iframe_height = models.CharField(_("iframe高度"), max_length=50, default="600")
    
    # 分类和标签
    categories = models.ManyToManyField(GameCategory, verbose_name=_("游戏分类"), related_name="games")
    tags = models.ManyToManyField(GameTag, verbose_name=_("游戏标签"), related_name="games", blank=True)
    
    # 统计和状态
    rating = models.DecimalField(_("评分"), max_digits=3, decimal_places=1, default=0)
    play_count = models.IntegerField(_("游玩次数"), default=0)
    is_featured = models.BooleanField(_("是否推荐"), default=False)
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default="offline")
    
    # SEO相关字段
    meta_title = models.CharField(_('Meta标题'), max_length=200, blank=True)
    meta_description = models.TextField(_('Meta描述'), blank=True)
    meta_keywords = models.CharField(_('Meta关键词'), max_length=500, blank=True)
    
    # 时间字段
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("游戏")
        verbose_name_plural = _("游戏")
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug or self.slug.startswith('-'):
            # 确保生成有意义的slug，使用title作为基础
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            if not base_slug:
                # 如果标题不能生成有效的slug（如纯中文标题），则使用拼音或首字母
                from django.utils.crypto import get_random_string
                import hashlib
                # 使用标题的哈希值前8位作为slug
                hash_obj = hashlib.md5(self.title.encode('utf-8'))
                base_slug = hash_obj.hexdigest()[:8]
            
            # 尝试使用基础slug，如果已存在则添加随机字符串
            self.slug = base_slug
            counter = 1
            while Game.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                # 如果slug已存在，则添加数字后缀
                self.slug = f"{base_slug}-{counter}"
                counter += 1
                
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """兼容前台代码的属性"""
        return self.status == 'online'


class SubscriptionPlan(models.Model):
    """会员订阅计划模型"""
    name = models.CharField(_("计划名称"), max_length=100)
    price = models.DecimalField(_("价格"), max_digits=10, decimal_places=2)
    period = models.CharField(_("周期"), max_length=20, choices=[
        ('monthly', _('月度')),
        ('yearly', _('年度')),
        ('quarterly', _('季度')),
        ('one_time', _('一次性')),
    ])
    description = models.TextField(_("描述"), blank=True)
    is_active = models.BooleanField(_("是否启用"), default=True)
    features = models.TextField(_("包含功能"), blank=True, help_text=_("每行一个功能点，将显示在前台"))
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("订阅计划")
        verbose_name_plural = _("订阅计划")
        ordering = ['price', 'id']

    def __str__(self):
        return f"{self.name} ({self.get_period_display()}: ${self.price})"


class PaymentGateway(models.Model):
    """支付网关模型"""
    GATEWAY_TYPES = [
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('alipay', '支付宝'),
        ('wechat', '微信支付'),
        ('braintree', 'Braintree'),
        ('adyen', 'Adyen'),
    ]
    
    name = models.CharField(_("网关名称"), max_length=100)
    gateway_type = models.CharField(_("网关类型"), max_length=20, choices=GATEWAY_TYPES)
    is_active = models.BooleanField(_("是否启用"), default=False)
    is_default = models.BooleanField(_("是否默认"), default=False)
    test_mode = models.BooleanField(_("测试模式"), default=True)
    config = models.JSONField(_("配置信息"), default=dict, blank=True, 
                             help_text=_("存储网关配置信息，内容根据网关类型不同"))
    display_order = models.IntegerField(_("显示顺序"), default=0)
    success_url = models.CharField(_("支付成功跳转URL"), max_length=255, default='/payment-success/')
    cancel_url = models.CharField(_("取消支付跳转URL"), max_length=255, default='/payment-cancel/')
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("支付网关")
        verbose_name_plural = _("支付网关")
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"{self.name} ({self.get_gateway_type_display()})"
    
    def save(self, *args, **kwargs):
        # 如果设置为默认，则取消其他网关的默认状态
        if self.is_default:
            PaymentGateway.objects.filter(gateway_type=self.gateway_type, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class Subscription(models.Model):
    """用户订阅模型"""
    STATUS_CHOICES = [
        ('active', _('活跃')),
        ('trial', _('试用期')),
        ('expired', _('已过期')),
        ('cancelled', _('已取消')),
        ('pending', _('待处理')),
        ('suspended', _('已暂停')),
    ]
    
    user = models.ForeignKey('auth.User', verbose_name=_("用户"), on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, verbose_name=_("订阅计划"), on_delete=models.PROTECT)
    start_date = models.DateTimeField(_("开始日期"), default=timezone.now)
    end_date = models.DateTimeField(_("结束日期"))
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_gateway = models.ForeignKey(PaymentGateway, verbose_name=_("支付网关"), 
                                       on_delete=models.SET_NULL, null=True, blank=True)
    gateway_subscription_id = models.CharField(_("网关订阅ID"), max_length=255, blank=True, 
                                             help_text=_("支付网关返回的订阅ID"))
    auto_renew = models.BooleanField(_("自动续费"), default=False)
    is_trial = models.BooleanField(_("是否试用"), default=False)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _("用户订阅")
        verbose_name_plural = _("用户订阅")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.get_status_display()})"

    def is_active(self):
        """检查订阅是否有效"""
        return self.status in ['active', 'trial'] and self.end_date > timezone.now()


class PaymentTransaction(models.Model):
    """支付交易记录模型"""
    TRANSACTION_STATUS = [
        ('pending', _('处理中')),
        ('success', _('成功')),
        ('failed', _('失败')),
        ('refunded', _('已退款')),
        ('partial_refund', _('部分退款')),
        ('cancelled', _('已取消')),
    ]
    
    TRANSACTION_TYPE = [
        ('subscription', _('会员订阅')),
        ('renewal', _('续费')),
        ('upgrade', _('升级')),
        ('downgrade', _('降级')),
        ('refund', _('退款')),
    ]
    
    user = models.ForeignKey('auth.User', verbose_name=_("用户"), on_delete=models.CASCADE, related_name="payment_transactions")
    subscription = models.ForeignKey(Subscription, verbose_name=_("关联订阅"), on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name="transactions")
    gateway = models.ForeignKey(PaymentGateway, verbose_name=_("支付网关"), on_delete=models.PROTECT)
    amount = models.DecimalField(_("金额"), max_digits=10, decimal_places=2)
    currency = models.CharField(_("货币"), max_length=3, default="USD")
    status = models.CharField(_("状态"), max_length=20, choices=TRANSACTION_STATUS, default='pending')
    transaction_type = models.CharField(_("交易类型"), max_length=20, choices=TRANSACTION_TYPE)
    gateway_transaction_id = models.CharField(_("网关交易ID"), max_length=255, blank=True)
    gateway_response = models.JSONField(_("网关响应"), default=dict, blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _("支付交易")
        verbose_name_plural = _("支付交易")
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()} ({self.amount} {self.currency})"
