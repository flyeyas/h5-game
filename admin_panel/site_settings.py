from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings
import os

class SiteSettings(models.Model):
    """网站基本设置模型"""
    # 网站基本信息
    site_name = models.CharField(_('网站名称'), max_length=100)
    site_description = models.TextField(_('网站描述'), blank=True)
    site_keywords = models.CharField(_('网站关键词'), max_length=255, blank=True, 
                                    help_text=_('多个关键词请用英文逗号分隔'))
    
    # 网站Logo和图标
    site_logo = models.ImageField(_('网站Logo'), upload_to='site_settings/', blank=True, null=True)
    site_favicon = models.ImageField(_('网站图标'), upload_to='site_settings/', blank=True, null=True, 
                                   help_text=_('推荐尺寸: 32x32 像素, 格式: .ico, .png'))
    
    # 创建和更新时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('网站设置')
        verbose_name_plural = _('网站设置')
    
    def __str__(self):
        return self.site_name
    
    @classmethod
    def get_settings(cls):
        """获取网站设置，优先从缓存中获取"""
        # 尝试从缓存获取
        settings = cache.get('site_settings')
        if not settings:
            # 如果缓存中没有，从数据库获取
            settings, created = cls.objects.get_or_create(
                pk=1,
                defaults={
                    'site_name': 'HTML5游戏平台',
                    'site_description': '最好玩的HTML5游戏平台，提供各类精品小游戏，让您随时随地享受游玩乐趣。',
                    'site_keywords': 'HTML5游戏,小游戏,网页游戏,手机游戏,休闲游戏'
                }
            )
            # 存入缓存
            cache.set('site_settings', settings, 3600)  # 缓存1小时
        return settings
    
    def save(self, *args, **kwargs):
        """重写保存方法，清除缓存"""
        super().save(*args, **kwargs)
        # 清除缓存
        cache.delete('site_settings') 