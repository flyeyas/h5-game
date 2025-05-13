"""
前台游戏模型模块 - 使用核心模型替代原有模型
使用从core导入的模型，保持前台代码的独立性
"""

# 从核心模块导入共享模型，保留当前模型名称
from core.models import Game, GameCategory, GameTag
# 不再从core导入用户相关模型
# from core.user_models import UserGameFavorite, GameComment, UserGameHistory

# 提供命名空间导入的兼容性
__all__ = [
    'Game', 
    'GameCategory', 
    'GameTag',
    'FrontUser',
    'FrontGameFavorite',
    'FrontGameHistory',
    'FrontGameComment',
    'FrontMenu',
    'MembershipFeature',
    'UserProfile'
]

# 重要：此文件不应有任何新的模型定义，只用于导入和重导出核心模型
# 这样可以保证前台代码只需引用 games.models，而不需要关心具体实现在哪里

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
import logging

# 导入信号处理相关
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.db.models.signals import post_save

logger = logging.getLogger(__name__)



# 自定义前台用户管理器
class FrontUserManager(BaseUserManager):
    """前台用户管理器"""
    def create_user(self, username, email, password=None, **extra_fields):
        """创建并保存普通用户"""
        if not email:
            raise ValueError(_('用户必须有邮箱地址'))
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        创建并保存前台超级用户 - 仅用于兼容Django命令
        前台用户不应该有superuser权限，此方法只是为了兼容
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self.create_user(username, email, password, **extra_fields)
    
    def active(self):
        """返回所有活跃的前台用户"""
        return self.filter(is_active=True)
    
    def with_game_data(self):
        """获取带有游戏相关数据的用户查询集"""
        return self.prefetch_related('game_favorites', 'game_history', 'game_comments')
    
    def members(self):
        """获取所有会员用户"""
        return self.filter(is_member=True, member_until__gt=timezone.now())

# 前台用户模型
class FrontUser(AbstractUser):
    """前台用户模型，用于普通用户账号"""
    email = models.EmailField(_('邮箱地址'), unique=True)
    avatar = models.ImageField(_('头像'), upload_to='users/avatars/', blank=True, null=True)
    is_member = models.BooleanField(_('是否是会员'), default=False)
    member_until = models.DateTimeField(_('会员截止日期'), blank=True, null=True)
    bio = models.TextField(_('个人简介'), blank=True, null=True)
    
    # 会员相关字段
    MEMBER_TYPES = (
        ('free', '免费用户'),
        ('monthly', '月度会员'),
        ('quarterly', '季度会员'),
        ('yearly', '年度会员'),
    )
    member_type = models.CharField(_('会员类型'), max_length=20, choices=MEMBER_TYPES, default='free')
    
    # 通知设置
    email_notifications = models.BooleanField(_('电子邮件通知'), default=True)
    game_updates = models.BooleanField(_('游戏更新通知'), default=True)
    subscription_alerts = models.BooleanField(_('订阅提醒'), default=True)
    marketing_emails = models.BooleanField(_('营销邮件'), default=False)
    
    # 隐私设置
    profile_visibility = models.BooleanField(_('个人资料可见性'), default=True)
    game_history_visibility = models.BooleanField(_('游戏历史可见性'), default=True)
    data_collection = models.BooleanField(_('数据收集'), default=True)
    
    # 游戏购买关联
    purchased_games = models.ManyToManyField('core.Game', verbose_name=_('已购买游戏'), related_name='purchasers', blank=True)
    
    # 会员管理
    membership_status = models.CharField(_('会员状态'), max_length=20, default='inactive')
    membership_start_date = models.DateTimeField(_('会员开始日期'), null=True, blank=True)
    membership_renewal_date = models.DateTimeField(_('会员续费日期'), null=True, blank=True)
    billing_cycle = models.CharField(_('计费周期'), max_length=20, default='monthly')
    
    # 用户偏好
    preferred_categories = models.ManyToManyField('core.GameCategory', verbose_name=_('偏好游戏分类'), related_name='preferred_by_users', blank=True)
    preferred_tags = models.ManyToManyField('core.GameTag', verbose_name=_('偏好游戏标签'), related_name='preferred_by_users', blank=True)
    
    # 用户认证
    email_verified = models.BooleanField(_('邮箱已验证'), default=False)
    verification_token = models.CharField(_('验证令牌'), max_length=100, blank=True, null=True)
    verification_token_created = models.DateTimeField(_('验证令牌创建时间'), blank=True, null=True)
    
    # 两步验证
    two_factor_enabled = models.BooleanField(_('是否启用两步验证'), default=False)
    two_factor_secret = models.CharField(_('两步验证密钥'), max_length=100, blank=True, null=True)
    
    # 用户权限和角色
    is_premium = models.BooleanField(_('高级用户'), default=False, help_text=_('高级用户可以访问特殊功能'))
    role = models.CharField(_('用户角色'), max_length=20, default='user', choices=(
        ('user', '普通用户'),
        ('moderator', '版主'),
        ('contributor', '贡献者'),
        ('vip', 'VIP用户'),
    ))
    
    # 账号安全
    last_password_change = models.DateTimeField(_('上次密码修改时间'), blank=True, null=True)
    login_attempts = models.PositiveSmallIntegerField(_('登录尝试次数'), default=0)
    last_login_attempt = models.DateTimeField(_('上次登录尝试时间'), blank=True, null=True)
    account_locked_until = models.DateTimeField(_('账号锁定截止时间'), blank=True, null=True)
    
    # 会话管理
    session_key = models.CharField(_('会话密钥'), max_length=40, blank=True, null=True)
    
    # 社交信息
    social_links = models.JSONField(_('社交账号链接'), default=dict, blank=True)
    
    # 用户配置
    preferences = models.JSONField(_('用户偏好设置'), default=dict, blank=True)
    
    # 为了解决与其他用户模型的冲突，添加related_name
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='front_user_set',
        related_query_name='front_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='front_user_set',
        related_query_name='front_user',
    )
    
    objects = FrontUserManager()

    class Meta:
        verbose_name = _('前台用户')
        verbose_name_plural = _('前台用户')
        db_table = 'games_front_user'  # 明确指定表名，与旧表区分开
        
    def __str__(self):
        return self.username
        
    def get_absolute_url(self):
        """获取用户个人资料页面URL"""
        return reverse('games:profile')
        
    def get_member_type_display(self):
        """获取会员类型显示名称"""
        return dict(self.MEMBER_TYPES).get(self.member_type, '未知')
    
    def is_membership_active(self):
        """检查用户会员状态是否有效"""
        if not self.is_member:
            return False
        if not self.member_until:
            return False
        return self.member_until > timezone.now()
    
    def get_favorite_games(self):
        """获取用户收藏的游戏"""
        return Game.objects.filter(front_favorited_by__user=self)
    
    def extend_membership(self, days):
        """延长会员有效期"""
        if not self.is_member:
            self.is_member = True
            self.membership_status = 'active'
            self.membership_start_date = timezone.now()
            self.member_until = timezone.now() + timezone.timedelta(days=days)
        else:
            # 如果会员已过期，从现在开始计算
            if self.member_until and self.member_until < timezone.now():
                self.member_until = timezone.now() + timezone.timedelta(days=days)
            # 否则在现有时间基础上延长
            elif self.member_until:
                self.member_until += timezone.timedelta(days=days)
            else:
                self.member_until = timezone.now() + timezone.timedelta(days=days)
        
        self.membership_renewal_date = timezone.now()
        self.save(update_fields=['is_member', 'membership_status', 'membership_start_date', 
                                'member_until', 'membership_renewal_date'])
    
    def cancel_membership(self):
        """取消会员资格"""
        self.is_member = False
        self.membership_status = 'cancelled'
        self.save(update_fields=['is_member', 'membership_status'])
    
    def get_recent_game_history(self, limit=5):
        """获取用户最近的游戏历史"""
        return self.game_history.all().select_related('game').order_by('-last_played')[:limit]
    
    def has_purchased_game(self, game):
        """检查用户是否已购买指定游戏"""
        return self.purchased_games.filter(id=game.id).exists()
    
    def favorite_game(self, game):
        """收藏游戏"""
        favorite, created = FrontGameFavorite.objects.get_or_create(user=self, game=game)
        return created
    
    def unfavorite_game(self, game):
        """取消收藏游戏"""
        deleted, _ = FrontGameFavorite.objects.filter(user=self, game=game).delete()
        return deleted > 0
    
    def is_game_favorite(self, game):
        """检查游戏是否被用户收藏"""
        return FrontGameFavorite.objects.filter(user=self, game=game).exists()
    
    def log_game_play(self, game):
        """记录游戏游玩"""
        history, created = FrontGameHistory.objects.get_or_create(user=self, game=game)
        if not created:
            history.play_count += 1
            history.save(update_fields=['play_count', 'last_played'])
        return history
    
    def generate_verification_token(self):
        """生成邮箱验证令牌"""
        import uuid
        self.verification_token = str(uuid.uuid4())
        self.verification_token_created = timezone.now()
        self.save(update_fields=['verification_token', 'verification_token_created'])
        return self.verification_token
    
    def verify_email(self, token):
        """验证用户邮箱"""
        if not self.verification_token or self.verification_token != token:
            return False
        
        # 检查令牌是否过期(24小时)
        if not self.verification_token_created or \
           (timezone.now() - self.verification_token_created).total_seconds() > 86400:
            return False
        
        self.email_verified = True
        self.verification_token = None
        self.verification_token_created = None
        self.save(update_fields=['email_verified', 'verification_token', 'verification_token_created'])
        return True
    
    def is_account_locked(self):
        """检查账号是否被锁定"""
        if not self.account_locked_until:
            return False
        return self.account_locked_until > timezone.now()
    
    def record_login_attempt(self, success=False):
        """记录登录尝试"""
        now = timezone.now()
        self.last_login_attempt = now
        
        if success:
            # 成功登录，重置尝试次数
            self.login_attempts = 0
            self.account_locked_until = None
        else:
            # 失败登录，增加尝试次数
            self.login_attempts += 1
            
            # 若尝试次数达到5次，锁定账号15分钟
            if self.login_attempts >= 5:
                self.account_locked_until = now + timedelta(minutes=15)
                logger.warning(f"用户账号被锁定: user_id={self.id}, username={self.username}")
        
        # 保存更改
        self.save(update_fields=['login_attempts', 'last_login_attempt', 'account_locked_until'])
        
        return not self.is_account_locked()
    
    def update_session_key(self, session_key):
        """更新用户当前的会话密钥"""
        self.session_key = session_key
        self.save(update_fields=['session_key'])
        
    def clear_session(self):
        """清除用户会话"""
        if self.session_key:
            from django.contrib.sessions.models import Session
            try:
                Session.objects.filter(session_key=self.session_key).delete()
            except Exception as e:
                logger.error(f"清除用户会话失败: user_id={self.id}, error={str(e)}")
        
        self.session_key = None
        self.save(update_fields=['session_key'])
    
    def record_password_change(self):
        """记录密码修改"""
        self.last_password_change = timezone.now()
        self.save(update_fields=['last_password_change'])
    
    def is_moderator(self):
        """检查用户是否是版主"""
        return self.role == 'moderator'
    
    def is_contributor(self):
        """检查用户是否是贡献者"""
        return self.role == 'contributor'
    
    def is_vip(self):
        """检查用户是否是VIP用户"""
        return self.role == 'vip'
    
    def get_social_link(self, platform):
        """获取指定平台的社交链接"""
        if not self.social_links:
            return None
        return self.social_links.get(platform)
    
    def set_social_link(self, platform, link):
        """设置指定平台的社交链接"""
        if not self.social_links:
            self.social_links = {}
        self.social_links[platform] = link
        self.save(update_fields=['social_links'])
    
    def get_preference(self, key, default=None):
        """获取用户偏好设置"""
        if not self.preferences:
            return default
        return self.preferences.get(key, default)
    
    def set_preference(self, key, value):
        """设置用户偏好设置"""
        if not self.preferences:
            self.preferences = {}
        self.preferences[key] = value
        self.save(update_fields=['preferences'])

# 已移除 UserGameFavorite 模型，改为从core.user_models导入

# 已移除 GameComment 模型，改为从core.user_models导入  

# 已移除 UserGameHistory 模型，改为从core.user_models导入

class FrontMenuManager(models.Manager):
    """
    前台菜单管理器，提供菜单相关的查询方法
    """
    def get_active_menus(self):
        """
        获取所有启用的菜单
        """
        return self.filter(is_active=True).order_by('order', 'id')
    
    def get_menu_tree(self):
        """
        获取菜单树结构
        """
        # 获取所有启用的菜单
        all_menus = self.get_active_menus()
        
        # 构建菜单树
        menu_tree = []
        menu_dict = {menu.id: menu for menu in all_menus}
        
        # 添加顶级菜单
        for menu in all_menus:
            if menu.parent is None:
                menu_tree.append(menu)
        
        return menu_tree


class FrontMenu(models.Model):
    """
    前台菜单模型 - 用于管理前台导航菜单
    """
    name = models.CharField(_('菜单名称'), max_length=50)
    url = models.CharField(_('链接URL'), max_length=200)
    icon = models.CharField(_('图标'), max_length=50, blank=True, help_text=_('Bootstrap Icon图标类名，例如：bi bi-house'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name=_('父级菜单'))
    order = models.IntegerField(_('排序'), default=0, help_text=_('数字越小排序越靠前'))
    is_active = models.BooleanField(_('是否启用'), default=True)
    is_external = models.BooleanField(_('是否外部链接'), default=False, help_text=_('勾选表示链接会在新窗口打开'))
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    # 使用自定义管理器
    objects = FrontMenuManager()
    
    class Meta:
        verbose_name = _('前台菜单')
        verbose_name_plural = _('前台菜单')
        ordering = ['order', 'id']
    
    def __str__(self):
        return self.name

    @property
    def level(self):
        """
        获取当前菜单的层级
        0表示顶级菜单，1表示二级菜单，以此类推
        """
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level
    
    def get_children(self):
        """
        获取当前菜单的所有直接子菜单
        """
        return FrontMenu.objects.filter(parent=self, is_active=True).order_by('order', 'id')
    
    def has_children(self):
        """
        检查当前菜单是否有子菜单
        """
        return self.children.filter(is_active=True).exists()
    
    def get_menu_tree(self):
        """
        获取以当前菜单为根的菜单树
        """
        return self.get_children()

class FrontGameFavorite(models.Model):
    """前台用户游戏收藏模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("用户"), on_delete=models.CASCADE, related_name="game_favorites")
    game = models.ForeignKey('core.Game', verbose_name=_("游戏"), on_delete=models.CASCADE, related_name="front_favorited_by")
    created_at = models.DateTimeField(_("收藏时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("前台游戏收藏")
        verbose_name_plural = _("前台游戏收藏")
        unique_together = ('user', 'game')

    def __str__(self):
        return f"{self.user.username} - {self.game.title}"
    
    @classmethod
    def toggle_favorite(cls, user, game):
        """切换游戏收藏状态"""
        try:
            favorite = cls.objects.get(user=user, game=game)
            favorite.delete()
            return False  # 返回False表示取消收藏
        except cls.DoesNotExist:
            cls.objects.create(user=user, game=game)
            return True  # 返回True表示添加收藏


class FrontGameHistory(models.Model):
    """前台用户游戏历史记录"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("用户"), on_delete=models.CASCADE, related_name="game_history")
    game = models.ForeignKey('core.Game', verbose_name=_("游戏"), on_delete=models.CASCADE, related_name="front_history")
    last_played = models.DateTimeField(_("最后游玩时间"), auto_now=True)
    play_count = models.IntegerField(_("游玩次数"), default=1)
    play_time = models.PositiveIntegerField(_("总游玩时间(分钟)"), default=0)
    completed = models.BooleanField(_("是否通关"), default=False)

    class Meta:
        verbose_name = _("前台游戏历史")
        verbose_name_plural = _("前台游戏历史")
        unique_together = ('user', 'game')
        ordering = ['-last_played']

    def __str__(self):
        return f"{self.user.username} - {self.game.title}"
    
    def log_play_time(self, minutes):
        """记录游玩时间"""
        self.play_time += minutes
        self.save(update_fields=['play_time', 'last_played'])
    
    @classmethod
    def log_game_play(cls, user, game, play_time=None):
        """记录游戏游玩，增加游玩次数"""
        history, created = cls.objects.get_or_create(user=user, game=game)
        history.play_count += 1
        
        if play_time is not None and isinstance(play_time, int) and play_time > 0:
            history.play_time += play_time
            
        history.save(update_fields=['play_count', 'last_played', 'play_time'])
        return history
    
    @classmethod
    def mark_completed(cls, user, game):
        """标记游戏为已通关"""
        history, created = cls.objects.get_or_create(user=user, game=game)
        history.completed = True
        history.save(update_fields=['completed', 'last_played'])
        return history

class FrontGameComment(models.Model):
    """前台游戏评论模型"""
    RATING_CHOICES = (
        (1, '1星'),
        (2, '2星'),
        (3, '3星'),
        (4, '4星'),
        (5, '5星'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("用户"), on_delete=models.CASCADE, related_name="game_comments")
    game = models.ForeignKey('core.Game', verbose_name=_("游戏"), on_delete=models.CASCADE, related_name="front_comments")
    rating = models.PositiveSmallIntegerField(_("评分"), choices=RATING_CHOICES, default=5)
    content = models.TextField(_("评论内容"))
    parent = models.ForeignKey('self', verbose_name=_("父评论"), on_delete=models.CASCADE, 
                              null=True, blank=True, related_name="replies")
    likes = models.JSONField(_("点赞用户"), default=list, blank=True)
    is_active = models.BooleanField(_("是否显示"), default=True)
    created_at = models.DateTimeField(_("评论时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True, null=True)

    class Meta:
        verbose_name = _("前台游戏评论")
        verbose_name_plural = _("前台游戏评论")
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.game.title} - {self.rating}星"
    
    def toggle_like(self, user_id):
        """切换点赞状态"""
        likes = self.likes or []
        if user_id in likes:
            likes.remove(user_id)
            liked = False
        else:
            likes.append(user_id)
            liked = True
        
        self.likes = likes
        self.save(update_fields=['likes'])
        return liked
    
    def like_count(self):
        """获取点赞数量"""
        return len(self.likes or [])
    
    def is_liked_by(self, user_id):
        """检查是否被指定用户点赞"""
        return user_id in (self.likes or [])
    
    def get_replies(self):
        """获取评论回复"""
        return self.replies.filter(is_active=True)

class MembershipFeature(models.Model):
    """会员特权模型"""
    MEMBERSHIP_LEVELS = (
        (1, '基础会员'),
        (2, '高级会员'),
        (3, '终极会员'),
    )
    
    name = models.CharField(_("特权名称"), max_length=100)
    description = models.TextField(_("特权描述"))
    membership_level = models.PositiveSmallIntegerField(_("会员等级要求"), choices=MEMBERSHIP_LEVELS)
    is_active = models.BooleanField(_("是否启用"), default=True)
    icon = models.CharField(_("特权图标"), max_length=50, blank=True, help_text=_('Bootstrap Icon图标类名，例如：bi bi-star'))
    priority = models.PositiveSmallIntegerField(_("显示优先级"), default=0, help_text=_('数字越小优先级越高'))

    class Meta:
        verbose_name = _("会员特权")
        verbose_name_plural = _("会员特权")
        ordering = ['membership_level', 'priority', 'id']
        
    def __str__(self):
        return f"{self.get_membership_level_display()} - {self.name}"
    
    def get_membership_level_display(self):
        """获取会员等级显示名称"""
        return dict(self.MEMBERSHIP_LEVELS).get(self.membership_level, '未知')

# 用户资料模型 - 替代原来的前台用户模型
class UserProfile(models.Model):
    """用户资料模型，与Django默认User模型关联"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(_('头像'), upload_to='users/avatars/', blank=True, null=True)
    avatar_url = models.URLField(_('头像URL'), max_length=500, blank=True, null=True)
    bio = models.TextField(_('个人简介'), blank=True, null=True)
    
    # 会员相关字段
    is_member = models.BooleanField(_('是否是会员'), default=False)
    member_until = models.DateTimeField(_('会员截止日期'), blank=True, null=True)
    MEMBER_TYPES = (
        ('free', '免费用户'),
        ('monthly', '月度会员'),
        ('quarterly', '季度会员'),
        ('yearly', '年度会员'),
    )
    member_type = models.CharField(_('会员类型'), max_length=20, choices=MEMBER_TYPES, default='free')
    
    # 通知设置
    email_notifications = models.BooleanField(_('电子邮件通知'), default=True)
    game_updates = models.BooleanField(_('游戏更新通知'), default=True)
    subscription_alerts = models.BooleanField(_('订阅提醒'), default=True)
    marketing_emails = models.BooleanField(_('营销邮件'), default=False)
    
    # 隐私设置
    profile_visibility = models.BooleanField(_('个人资料可见性'), default=True)
    game_history_visibility = models.BooleanField(_('游戏历史可见性'), default=True)
    data_collection = models.BooleanField(_('数据收集'), default=True)
    
    # 游戏购买关联
    purchased_games = models.ManyToManyField('core.Game', verbose_name=_('已购买游戏'), related_name='profile_purchasers', blank=True)
    
    # 会员管理
    membership_status = models.CharField(_('会员状态'), max_length=20, default='inactive')
    membership_start_date = models.DateTimeField(_('会员开始日期'), null=True, blank=True)
    membership_renewal_date = models.DateTimeField(_('会员续费日期'), null=True, blank=True)
    billing_cycle = models.CharField(_('计费周期'), max_length=20, default='monthly')
    
    # 用户偏好
    preferred_categories = models.ManyToManyField('core.GameCategory', verbose_name=_('偏好游戏分类'), related_name='profile_preferred_by_users', blank=True)
    preferred_tags = models.ManyToManyField('core.GameTag', verbose_name=_('偏好游戏标签'), related_name='profile_preferred_by_users', blank=True)
    
    # 用户权限和角色
    is_premium = models.BooleanField(_('高级用户'), default=False, help_text=_('高级用户可以访问特殊功能'))
    role = models.CharField(_('用户角色'), max_length=20, default='user', choices=(
        ('user', '普通用户'),
        ('moderator', '版主'),
        ('contributor', '贡献者'),
        ('vip', 'VIP用户'),
    ))
    
    # 社交信息
    social_links = models.JSONField(_('社交账号链接'), default=dict, blank=True)
    
    # 用户配置
    preferences = models.JSONField(_('用户偏好设置'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('用户资料')
        verbose_name_plural = _('用户资料')
        db_table = 'games_user_profile'
        
    def __str__(self):
        return f"{self.user.username}的资料"
        
    def get_absolute_url(self):
        """获取用户个人资料页面URL"""
        return reverse('games:profile')
        
    def get_member_type_display(self):
        """获取会员类型显示名称"""
        return dict(self.MEMBER_TYPES).get(self.member_type, '未知')
    
    def is_membership_active(self):
        """检查用户会员状态是否有效"""
        if not self.is_member:
            return False
        if not self.member_until:
            return False
        return self.member_until > timezone.now()
    
    def get_favorite_games(self):
        """获取用户收藏的游戏"""
        return Game.objects.filter(front_favorited_by__user__profile=self)
    
    def is_game_favorite(self, game):
        """检查游戏是否被用户收藏"""
        return FrontGameFavorite.objects.filter(user__profile=self, game=game).exists()
    
    def get_social_link(self, platform):
        """获取指定平台的社交链接"""
        if not self.social_links:
            return None
        return self.social_links.get(platform)
    
    def set_social_link(self, platform, link):
        """设置指定平台的社交链接"""
        if not self.social_links:
            self.social_links = {}
        self.social_links[platform] = link
        self.save(update_fields=['social_links'])
    
    def get_preference(self, key, default=None):
        """获取用户偏好设置"""
        if not self.preferences:
            return default
        return self.preferences.get(key, default)
    
    def set_preference(self, key, value):
        """设置用户偏好设置"""
        if not self.preferences:
            self.preferences = {}
        self.preferences[key] = value
        self.save(update_fields=['preferences'])
        
    def is_vip(self):
        """检查用户是否是VIP用户"""
        return self.role == 'vip'

# 社交账号登录成功后创建用户资料信号处理
@receiver(user_signed_up)
def create_user_profile_for_social_user(sender, request, user, **kwargs):
    """
    当用户通过社交账号首次登录时创建用户资料
    """
    UserProfile.objects.get_or_create(user=user)
    
    # 如果是社交账号登录，尝试从OAuth获取头像
    if 'sociallogin' in kwargs:
        sociallogin = kwargs['sociallogin']
        if sociallogin.account.provider == 'google':
            try:
                # 获取Google资料图片
                avatar_url = sociallogin.account.extra_data.get('picture')
                if avatar_url:
                    # 更新用户资料的头像URL
                    profile = UserProfile.objects.get(user=user)
                    profile.avatar_url = avatar_url
                    profile.save()
            except Exception as e:
                # 记录错误但不中断流程
                import logging
                logger = logging.getLogger('games')
                logger.error(f"获取Google头像失败: {str(e)}")
