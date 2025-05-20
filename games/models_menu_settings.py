from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from filer.fields.image import FilerImageField


class Language(models.Model):
    """语言模型"""
    code = models.CharField(_('Language Code'), max_length=10, unique=True)
    name = models.CharField(_('Language Name'), max_length=100)
    flag = FilerImageField(verbose_name=_('Flag'), null=True, blank=True, 
                          on_delete=models.SET_NULL, related_name='language_flags')
    is_active = models.BooleanField(_('Active'), default=True)
    is_default = models.BooleanField(_('Default'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')
        ordering = ['code']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 如果当前语言设置为默认，则将其他语言设置为非默认
        if self.is_default:
            Language.objects.filter(is_default=True).update(is_default=False)
        # 如果没有默认语言，则将当前语言设置为默认
        elif not Language.objects.filter(is_default=True).exists():
            self.is_default = True
        super().save(*args, **kwargs)


class Menu(models.Model):
    """菜单模型"""
    MENU_TYPE_CHOICES = (
        ('header', _('Header Menu')),
        ('footer', _('Footer Menu')),
        ('sidebar', _('Sidebar Menu')),
        ('backend', _('Backend Menu')),
    )
    
    name = models.CharField(_('Menu Name'), max_length=100)
    menu_type = models.CharField(_('Menu Type'), max_length=20, choices=MENU_TYPE_CHOICES)
    order = models.IntegerField(_('Order'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Menu')
        verbose_name_plural = _('Menus')
        ordering = ['menu_type', 'order']
        unique_together = ['name', 'menu_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_menu_type_display()})"


class MenuItem(models.Model):
    """菜单项模型"""
    menu = models.ForeignKey(Menu, verbose_name=_('Menu'), on_delete=models.CASCADE, related_name='items')
    parent = models.ForeignKey('self', verbose_name=_('Parent Item'), null=True, blank=True, 
                              on_delete=models.CASCADE, related_name='children')
    title = models.CharField(_('Title'), max_length=100)
    url = models.CharField(_('URL'), max_length=200)
    icon = models.CharField(_('Icon'), max_length=50, blank=True, help_text=_('Font Awesome icon class name'))
    target = models.CharField(_('Target'), max_length=10, choices=(('_self', _('Current Window')), ('_blank', _('New Window'))), default='_self')
    order = models.IntegerField(_('Order'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)
    permission_required = models.CharField(_('Permission Required'), max_length=100, blank=True, 
                                         help_text=_('Django permission format, e.g.: app.add_model'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Menu Item')
        verbose_name_plural = _('Menu Items')
        ordering = ['menu', 'order']
    
    def __str__(self):
        return self.title


class WebsiteSetting(models.Model):
    """网站设置模型"""
    site_name = models.CharField(_('Site Name'), max_length=100)
    site_description = models.TextField(_('Site Description'))
    logo = FilerImageField(verbose_name=_('Site Logo'), null=True, blank=True, 
                          on_delete=models.SET_NULL, related_name='site_logos')
    favicon = FilerImageField(verbose_name=_('Favicon'), null=True, blank=True,
                            on_delete=models.SET_NULL, related_name='site_favicons')
    email = models.EmailField(_('Contact Email'), blank=True)
    phone = models.CharField(_('Contact Phone'), max_length=20, blank=True)
    address = models.TextField(_('Address'), blank=True)
    copyright_text = models.CharField(_('Copyright Text'), max_length=200, blank=True)
    facebook_url = models.URLField(_('Facebook URL'), blank=True)
    twitter_url = models.URLField(_('Twitter URL'), blank=True)
    instagram_url = models.URLField(_('Instagram URL'), blank=True)
    youtube_url = models.URLField(_('YouTube URL'), blank=True)
    meta_keywords = models.TextField(_('Meta Keywords'), blank=True, help_text=_('SEO keywords separated by commas'))
    meta_description = models.TextField(_('Meta Description'), blank=True, help_text=_('SEO description'))
    google_analytics_code = models.TextField(_('Google Analytics Code'), blank=True)
    # 多语言设置
    enable_language_switcher = models.BooleanField(_('Enable Language Switcher'), default=True, 
                                                 help_text=_('Show language switcher in the site header'))
    auto_detect_language = models.BooleanField(_('Auto-detect User Language'), default=False,
                                              help_text=_('Automatically detect and use the user\'s browser language if available'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Website Setting')
        verbose_name_plural = _('Website Settings')
    
    def __str__(self):
        return self.site_name
    
    @classmethod
    def get_settings(cls):
        """获取网站设置，如果不存在则创建默认设置"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'HTML5 Games',
                'site_description': 'Play free HTML5 games online!',
                'copyright_text': f'© {timezone.now().year} HTML5 Games. All rights reserved.'
            }
        )
        return settings