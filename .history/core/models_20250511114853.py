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
