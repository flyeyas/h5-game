from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager, User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import PermissionDenied

# 管理员角色选项
ROLE_CHOICES = (
    ('super_admin', _('超级管理员')),
    ('content_admin', _('内容管理员')),
    ('user_admin', _('用户管理员')),
    ('game_admin', _('游戏管理员')),
    ('analyst', _('数据分析师')),
    ('support', _('客服')),
)

# 管理员状态选项
STATUS_CHOICES = (
    ('active', _('活跃')),
    ('inactive', _('禁用')),
    ('pending', _('待审核')),
)

# 修改User.delete()方法，阻止删除ID为1的用户
original_delete = User.delete

def delete_with_protection(self, *args, **kwargs):
    """装饰User.delete方法，保护ID为1的超级管理员"""
    if self.id == 1:
        raise PermissionDenied("系统超级管理员(ID=1)不允许被删除")
    return original_delete(self, *args, **kwargs)

# 替换User.delete方法
User.delete = delete_with_protection

# 注释掉自定义用户管理器，使用Django默认的User模型
"""
class AdminUserManager(BaseUserManager):
    # 管理员用户管理器，提供管理员相关的查询方法
    def filter_active_admins(self):
        # 获取所有活跃的管理员
        return self.filter(status='active')
    
    def filter_admins_by_role(self, role):
        # 根据角色获取管理员
        return self.filter(role=role)
        
    def get_admin_by_username(self, username):
        # 根据用户名获取用户，Django认证后端需要此方法
        return self.get(username=username)
    
    def get_by_natural_key(self, username):
        # 通过自然键（用户名）获取用户，Django认证系统需要此方法
        return self.get(username=username)
    
    def normalize_email(self, email):
        # 规范化邮箱地址，Django用户模型需要此方法
        return BaseUserManager.normalize_email(email)
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        # 创建普通用户
        if not username:
            raise ValueError('必须提供用户名')
        
        if email:
            email = self.normalize_email(email)
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # 创建超级用户
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 10)  # Super Admin
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')
        
        return self.create_user(username, email, password, **extra_fields)
"""

# 用户角色和权限相关模型
class Permission(models.Model):
    """权限定义模型"""
    CATEGORY_CHOICES = (
        ('content', '内容管理'),
        ('game', '游戏管理'),
        ('user', '用户管理'),
        ('system', '系统设置'),
    )
    
    name = models.CharField(max_length=100, unique=True, verbose_name='权限名称')
    codename = models.CharField(max_length=100, unique=True, verbose_name='权限代码')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='content', verbose_name='权限分类')
    description = models.TextField(blank=True, null=True, verbose_name='权限描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '权限'
        verbose_name_plural = '权限'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Role(models.Model):
    """用户角色模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='角色名称')
    description = models.TextField(blank=True, null=True, verbose_name='角色描述')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles', verbose_name='权限')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# 管理员用户信息扩展模型，与Django默认User模型关联
class AdminProfile(models.Model):
    """管理员用户信息扩展模型"""
    ROLES = (
        (10, 'Super Admin'),
        (20, 'Admin'),
        (30, 'Content Editor'),
        (40, 'Agent'),
    )
    
    STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile', verbose_name=_('用户'))
    role = models.IntegerField(choices=ROLES, default=40, verbose_name=_('角色类型'))
    status = models.CharField(max_length=10, choices=STATUS, default='active', verbose_name=_('状态'))
    custom_permissions = models.ManyToManyField(Permission, blank=True, related_name='admin_users_with_permission', verbose_name=_('自定义权限'))
    
    # 基本信息
    real_name = models.CharField(_('姓名'), max_length=50, blank=True)
    avatar = models.ImageField(_('头像'), upload_to='admin/avatars/', blank=True, null=True)
    avatar_url = models.URLField(_('头像URL'), max_length=500, blank=True, null=True)
    mobile = models.CharField(_('手机号'), max_length=20, blank=True)
    
    # 时间记录
    last_login_time = models.DateTimeField(_('最后登录时间'), blank=True, null=True)
    created_time = models.DateTimeField(_('创建时间'), default=timezone.now)
    
    # 备注
    notes = models.TextField(_('备注'), blank=True)
    
    class Meta:
        verbose_name = _('管理员资料')
        verbose_name_plural = _('管理员资料列表')
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        """兼容性属性，返回用户的 is_staff 的值"""
        return self.user.is_staff
    
    def has_permission(self, permission_code):
        """
        检查用户是否拥有指定权限
        
        Args:
            permission_code: 权限代码
            
        Returns:
            bool: 是否拥有权限
        """
        # 超级管理员拥有所有权限
        if self.user.is_superuser or self.role == 10:  # 10 = super_admin
            return True
            
        # 检查自定义权限
        custom_perms = self.custom_permissions.filter(codename=permission_code).exists()
        if custom_perms:
            return True
                
        # 检查组权限
        for group in self.user.groups.all():
            if group.permissions.filter(codename=permission_code).exists():
                return True
                
        return False

# 为兼容性提供一个别名，将AdminUser映射到Django的User模型
AdminUser = User