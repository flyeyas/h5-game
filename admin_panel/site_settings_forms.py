from django import forms
from django.utils.translation import gettext_lazy as _
from .site_settings import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    """网站设置表单"""
    
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_description', 'site_keywords',
            'site_logo', 'site_favicon',
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('例如：HTML5游戏平台')}),
            'site_description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': _('最好玩的HTML5游戏平台，提供各类精品小游戏，让您随时随地享受游玩乐趣。')
            }),
            'site_keywords': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('HTML5游戏,小游戏,网页游戏,手机游戏,休闲游戏')
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 为必填字段添加required类
        self.fields['site_name'].widget.attrs.update({'required': True})
        
        # 添加帮助文本
        self.fields['site_logo'].help_text = _('推荐尺寸: 200x60 像素')
        self.fields['site_favicon'].help_text = _('推荐尺寸: 32x32 像素, 格式: .ico, .png')
        self.fields['site_keywords'].help_text = _('多个关键词请用英文逗号分隔') 