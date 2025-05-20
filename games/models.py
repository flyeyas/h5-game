from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from cms.models.fields import PlaceholderField
from filer.fields.image import FilerImageField


class Category(models.Model):
    """游戏分类模型"""
    name = models.CharField(_('分类名称'), max_length=100)
    slug = models.SlugField(_('URL别名'), max_length=100, unique=True)
    description = models.TextField(_('分类描述'), blank=True)
    parent = models.ForeignKey('self', verbose_name=_('父级分类'), null=True, blank=True, 
                               on_delete=models.SET_NULL, related_name='children')
    image = FilerImageField(verbose_name=_('分类图片'), null=True, blank=True, 
                           on_delete=models.SET_NULL, related_name='category_images')
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
    thumbnail = FilerImageField(verbose_name=_('游戏缩略图'), null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='game_thumbnails')
    categories = models.ManyToManyField(Category, verbose_name=_('游戏分类'), related_name='games')
    content = PlaceholderField('game_content', verbose_name=_('游戏内容'))
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


class Membership(models.Model):
    """会员等级模型"""
    MEMBERSHIP_CHOICES = (
        ('free', _('免费会员')),
        ('basic', _('基础会员')),
        ('premium', _('高级会员')),
    )
    
    name = models.CharField(_('会员等级名称'), max_length=100)
    slug = models.SlugField(_('URL别名'), max_length=100, unique=True)
    level = models.CharField(_('等级类型'), max_length=20, choices=MEMBERSHIP_CHOICES, default='free')
    price = models.DecimalField(_('价格'), max_digits=10, decimal_places=2, default=0.0)
    duration_days = models.PositiveIntegerField(_('有效期(天)'), default=30)
    description = models.TextField(_('会员权益描述'))
    is_active = models.BooleanField(_('是否激活'), default=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('会员等级')
        verbose_name_plural = _('会员等级')
        ordering = ['price']
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """用户资料模型"""
    user = models.OneToOneField(User, verbose_name=_('用户'), on_delete=models.CASCADE, related_name='profile')
    avatar = FilerImageField(verbose_name=_('头像'), null=True, blank=True,
                            on_delete=models.SET_NULL, related_name='user_avatars')
    bio = models.TextField(_('个人简介'), blank=True)
    favorite_games = models.ManyToManyField(Game, verbose_name=_('收藏的游戏'), related_name='favorited_by')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('用户资料')
        verbose_name_plural = _('用户资料')
    
    def __str__(self):
        return self.user.username


class GameComment(models.Model):
    """游戏评论模型"""
    game = models.ForeignKey(Game, verbose_name=_('游戏'), on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, verbose_name=_('用户'), on_delete=models.CASCADE, related_name='game_comments')
    content = models.TextField(_('评论内容'))
    rating = models.PositiveSmallIntegerField(_('评分'), choices=[(i, i) for i in range(1, 6)], default=5)
    is_approved = models.BooleanField(_('是否审核通过'), default=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('游戏评论')
        verbose_name_plural = _('游戏评论')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.game.title}"


class GameHistory(models.Model):
    """游戏历史记录模型"""
    user = models.ForeignKey(User, verbose_name=_('用户'), on_delete=models.CASCADE, related_name='game_history')
    game = models.ForeignKey(Game, verbose_name=_('游戏'), on_delete=models.CASCADE, related_name='play_history')
    play_time = models.PositiveIntegerField(_('游戏时长(秒)'), default=0)
    played_at = models.DateTimeField(_('游玩时间'), auto_now_add=True)
    last_played = models.DateTimeField(_('最后游戏时间'), auto_now=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('游戏历史')
        verbose_name_plural = _('游戏历史')
        ordering = ['-last_played']
        unique_together = ['user', 'game']
    
    def __str__(self):
        return f'{self.user.username} - {self.game.title}'


class Advertisement(models.Model):
    """广告模型"""
    POSITION_CHOICES = (
        ('header', _('页面顶部')),
        ('sidebar', _('侧边栏')),
        ('game_between', _('游戏间隙')),
        ('footer', _('页面底部')),
    )
    
    name = models.CharField(_('广告名称'), max_length=100)
    position = models.CharField(_('广告位置'), max_length=20, choices=POSITION_CHOICES)
    image = FilerImageField(verbose_name=_('广告图片'), null=True, blank=True, 
                           on_delete=models.SET_NULL, related_name='ad_images')
    url = models.URLField(_('广告链接'))
    html_code = models.TextField(_('HTML代码'), blank=True, help_text=_('如果使用第三方广告代码，请填写此字段'))
    is_active = models.BooleanField(_('是否激活'), default=True)
    start_date = models.DateTimeField(_('开始日期'), null=True, blank=True)
    end_date = models.DateTimeField(_('结束日期'), null=True, blank=True)
    click_count = models.PositiveIntegerField(_('点击次数'), default=0)
    view_count = models.PositiveIntegerField(_('展示次数'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('广告')
        verbose_name_plural = _('广告')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name





