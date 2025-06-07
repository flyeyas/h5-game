from django.db import models
from django.utils.translation import gettext_lazy as _


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
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


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
    
    name = models.CharField(_('Advertisement Name'), max_length=100)
    position = models.CharField(_('Position'), max_length=20, choices=POSITION_CHOICES)
    image = models.ImageField(verbose_name=_('Advertisement Image'), upload_to='ads/', null=True, blank=True)
    url = models.URLField(_('Advertisement URL'))
    html_code = models.TextField(_('HTML Code'), blank=True, help_text=_('Fill this field if using third-party advertisement code'))
    is_active = models.BooleanField(_('Active'), default=True)
    start_date = models.DateTimeField(_('Start Date'), null=True, blank=True)
    end_date = models.DateTimeField(_('End Date'), null=True, blank=True)
    click_count = models.PositiveIntegerField(_('Click Count'), default=0)
    view_count = models.PositiveIntegerField(_('View Count'), default=0)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Advertisement')
        verbose_name_plural = _('Advertisements')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name





