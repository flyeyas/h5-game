from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from colorfield.fields import ColorField
from django.core.cache import cache
import json

# 导入管理员用户模型
# from .admin_user import AdminUser, ROLE_CHOICES, STATUS_CHOICES
from .admin_user import ROLE_CHOICES, STATUS_CHOICES
# 导入游戏分类模型
from .game_category import GameCategory
# 导入网站设置模型
from .site_settings import SiteSettings

# 管理员用户模型已移至 admin_user.py

# 角色模型(Role)，用于管理自定义角色和权限组
# Role模型将在下一次迁移中添加
# 暂时删除Role模型以避免冲突

# 管理员操作日志
class AdminLog(models.Model):
    """管理员操作日志"""
    admin = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('管理员'))
    action = models.CharField(_('操作'), max_length=200)
    ip_address = models.GenericIPAddressField(_('IP地址'), blank=True, null=True)
    created_at = models.DateTimeField(_('操作时间'), default=timezone.now, db_column='timestamp')
    
    class Meta:
        verbose_name = _('操作日志')
        verbose_name_plural = _('操作日志')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.admin.username} - {self.action}"


# 菜单模型已移至 menu.py

class SeoSettings(models.Model):
    """SEO设置"""
    page_type = models.CharField(_('页面类型'), max_length=50, unique=True, default='default')
    title_template = models.CharField(_('标题模板'), max_length=200, default='{页面名} - GameHub')
    description_template = models.TextField(_('描述模板'), default='{页面名}是GameHub的一部分，提供最好玩的HTML5游戏体验。')
    keywords = models.CharField(_('关键词'), max_length=500, blank=True, default='HTML5游戏,小游戏,休闲游戏')
    og_title_template = models.CharField(_('OG标题模板'), max_length=200, blank=True, default='')
    og_description_template = models.TextField(_('OG描述模板'), blank=True, default='')
    og_image = models.ImageField(_('OG图片'), upload_to='seo/', blank=True, null=True)
    
    class Meta:
        verbose_name = _('SEO设置')
        verbose_name_plural = _('SEO设置')
        
    def __str__(self):
        return self.page_type

class ConfigSettings(models.Model):
    """系统配置设置"""
    key = models.CharField(_('配置键'), max_length=50, unique=True)
    value = models.TextField(_('配置值'))
    description = models.CharField(_('配置描述'), max_length=200, blank=True)
    is_active = models.BooleanField(_('是否启用'), default=True)
    
    class Meta:
        verbose_name = _('系统配置')
        verbose_name_plural = _('系统配置')
        
    def __str__(self):
        return self.key

    @classmethod
    def get_config(cls, key, default=None):
        """获取配置，优先从缓存中获取"""
        cache_key = f'config__{key}'
        config = cache.get(cache_key)
        
        if config is None:
            # 缓存中没有，从数据库获取
            try:
                config_obj = cls.objects.get(key=key, is_active=True)
                config = config_obj.value
                
                # 尝试将字符串转换为JSON
                try:
                    import json
                    config = json.loads(config)
                except (json.JSONDecodeError, TypeError):
                    # 如果不是有效的JSON，保持字符串格式
                    pass
                    
                # 存入缓存
                cache.set(cache_key, config, 3600)  # 缓存1小时
            except cls.DoesNotExist:
                config = default
                
        return config
        
    def save(self, *args, **kwargs):
        """重写保存方法，清除缓存"""
        super().save(*args, **kwargs)
        
        # 清除缓存
        cache_key = f'config__{self.key}'
        cache.delete(cache_key)