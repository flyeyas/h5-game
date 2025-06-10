from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import hashlib
import uuid
import time


class Category(models.Model):
    """游戏分类模型"""
    name = models.CharField(_('分类名称'), max_length=100)
    slug = models.SlugField(_('URL别名'), max_length=100, unique=True)
    description = models.TextField(_('分类描述'), blank=True)
    parent = models.ForeignKey('self', verbose_name=_('父级分类'), null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='children')
    image = models.ImageField(verbose_name=_('分类图片'), upload_to='categories/', null=True, blank=True)
    icon_class = models.CharField(_('Icon Class'), max_length=100, blank=True, help_text=_('Font Awesome 6+ icon class, e.g., "fa-solid fa-gamepad"'))
    order = models.IntegerField(_('排序'), default=0)
    is_active = models.BooleanField(_('是否激活'), default=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('游戏分类')
        verbose_name_plural = _('游戏分类')
        ordering = ['id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        重写save方法，自动生成唯一的哈希串作为slug
        使用Django的slugify函数确保URL友好的格式
        """
        if not self.slug or self.slug.strip() == '':
            # 生成唯一的哈希串作为slug
            self.slug = self._generate_unique_hash_slug()

        super().save(*args, **kwargs)

    def _generate_unique_hash_slug(self):
        """
        生成唯一的哈希串作为slug
        结合分类名称、时间戳和UUID确保唯一性
        """
        # 创建用于哈希的原始字符串，包含分类名称、时间戳和随机UUID
        raw_string = f"{self.name}-{time.time()}-{uuid.uuid4().hex}"

        # 使用SHA256生成哈希值
        hash_object = hashlib.sha256(raw_string.encode('utf-8'))
        hash_hex = hash_object.hexdigest()

        # 取前12位作为slug（足够短且唯一性很高）
        hash_slug = hash_hex[:12]

        # 使用Django的slugify确保生成的哈希串是URL友好的
        # 虽然哈希串通常已经是URL友好的，但这样更安全
        slug = slugify(hash_slug)

        # 双重检查唯一性（理论上哈希冲突概率极低，但为了安全起见）
        counter = 1
        original_slug = slug
        while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = slugify(f"{original_slug}-{counter}")
            counter += 1

        return slug


class Game(models.Model):
    """游戏模型"""
    title = models.CharField(_('游戏标题'), max_length=200)
    slug = models.SlugField(_('URL别名'), max_length=200, unique=True)
    description = models.TextField(_('游戏描述'))
    iframe_url = models.URLField(_('游戏iframe地址'))
    thumbnail = models.ImageField(verbose_name=_('游戏缩略图'), upload_to='games/', null=True, blank=True)
    categories = models.ManyToManyField(Category, verbose_name=_('游戏分类'), related_name='games')
    content = models.TextField(_('游戏内容'), blank=True)
    is_featured = models.BooleanField(_('是否推荐'), default=False)
    is_active = models.BooleanField(_('是否激活'), default=True)
    view_count = models.PositiveIntegerField(_('浏览次数'), default=0)
    rating = models.DecimalField(_('评分'), max_digits=3, decimal_places=1, default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('游戏')
        verbose_name_plural = _('游戏')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

    @property
    def rating_int(self):
        """返回评分的整数部分"""
        return int(self.rating)

    @property
    def rating_int_plus_half(self):
        """返回评分的整数部分+0.5，用于显示半星"""
        return int(self.rating) + 1 if self.rating % 1 >= 0.5 else None


class Advertisement(models.Model):
    """Advertisement model"""
    POSITION_CHOICES = (
        ('header', _('Header')),
        ('sidebar', _('Sidebar')),
        ('game_between', _('Between Games')),
        ('footer', _('Footer')),
    )

    AD_TYPE_CHOICES = (
        ('display', _('Display Ad')),
        ('text', _('Text Ad')),
        ('native', _('Native Ad')),
        ('interstitial', _('Interstitial Ad')),
        ('video', _('Video Ad')),
    )

    AD_SIZE_CHOICES = (
        ('728x90', '728 x 90 (Leaderboard)'),
        ('300x250', '300 x 250 (Medium Rectangle)'),
        ('320x50', '320 x 50 (Mobile Banner)'),
        ('300x600', '300 x 600 (Half Page)'),
        ('970x250', '970 x 250 (Billboard)'),
        ('320x480', '320 x 480 (Mobile Interstitial)'),
        ('responsive', _('Responsive')),
        ('custom', _('Custom Size')),
    )

    # 基本信息
    name = models.CharField(_('Advertisement Name'), max_length=100)
    position = models.CharField(_('Position'), max_length=20, choices=POSITION_CHOICES)
    ad_type = models.CharField(_('Ad Type'), max_length=20, choices=AD_TYPE_CHOICES, default='display')
    ad_size = models.CharField(_('Ad Size'), max_length=20, choices=AD_SIZE_CHOICES, default='responsive')

    # 广告内容
    image = models.ImageField(verbose_name=_('Advertisement Image'), upload_to='ads/', null=True, blank=True)
    url = models.URLField(_('Advertisement URL'), blank=True)
    html_code = models.TextField(_('HTML Code'), blank=True, help_text=_('Fill this field if using third-party advertisement code'))

    # Google AdSense 相关字段
    adsense_unit_id = models.CharField(_('AdSense Unit ID'), max_length=100, blank=True, help_text=_('Google AdSense ad unit ID'))
    adsense_publisher_id = models.CharField(_('AdSense Publisher ID'), max_length=100, blank=True, help_text=_('Google AdSense publisher ID'))
    adsense_slot_id = models.CharField(_('AdSense Slot ID'), max_length=100, blank=True, help_text=_('Google AdSense slot ID'))

    # 状态和时间
    is_active = models.BooleanField(_('Active'), default=True)
    start_date = models.DateTimeField(_('Start Date'), null=True, blank=True)
    end_date = models.DateTimeField(_('End Date'), null=True, blank=True)

    # 统计数据
    click_count = models.PositiveIntegerField(_('Click Count'), default=0)
    view_count = models.PositiveIntegerField(_('View Count'), default=0)
    revenue = models.DecimalField(_('Revenue'), max_digits=10, decimal_places=2, default=0.00, help_text=_('Total revenue generated'))
    ctr = models.DecimalField(_('Click Through Rate'), max_digits=5, decimal_places=2, default=0.00, help_text=_('Click through rate percentage'))

    # 时间戳
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Advertisement')
        verbose_name_plural = _('Advertisements')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_position_display(self):
        """返回位置的显示名称"""
        for code, name in self.POSITION_CHOICES:
            if code == self.position:
                return name
        return self.position

    def has_image(self):
        """检查广告是否有图片"""
        return bool(self.image)

    def calculate_ctr(self):
        """计算点击率"""
        if self.view_count > 0:
            self.ctr = (self.click_count / self.view_count) * 100
        else:
            self.ctr = 0
        return self.ctr

    def get_ad_code(self):
        """获取广告代码"""
        if self.html_code:
            return self.html_code
        elif self.adsense_unit_id and self.adsense_publisher_id:
            # 生成Google AdSense代码
            return f'''
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={self.adsense_publisher_id}" crossorigin="anonymous"></script>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{self.adsense_publisher_id}"
     data-ad-slot="{self.adsense_slot_id}"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>
            '''.strip()
        return ''





