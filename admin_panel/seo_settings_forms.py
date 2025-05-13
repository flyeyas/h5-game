from django import forms
from django.utils.translation import gettext_lazy as _
from .models import SeoSettings

class SeoSettingsForm(forms.ModelForm):
    """SEO设置表单"""
    
    class Meta:
        model = SeoSettings
        fields = [
            'page_type', 'title_template', 'description_template',
            'keywords', 'og_title_template', 'og_description_template', 'og_image',
        ]
        widgets = {
            'page_type': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('例如：home, category, game_detail')
            }),
            'title_template': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('例如：{页面名称} - {网站名称}')
            }),
            'description_template': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': _('例如：{页面名称}是{网站名称}的一部分，提供最好玩的HTML5游戏体验。')
            }),
            'keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('关键词1,关键词2,关键词3')
            }),
            'og_title_template': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'og_description_template': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'og_image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 添加帮助文本
        self.fields['page_type'].help_text = _('页面类型标识符，用于区分不同页面的SEO配置')
        self.fields['title_template'].help_text = _('可用变量: {网站名}, {页面名}, {分类名}, {游戏名}')
        self.fields['description_template'].help_text = _('可用变量: {网站名}, {页面名}, {分类名}, {游戏名}, {描述}')
        self.fields['keywords'].help_text = _('用逗号分隔的关键词列表，建议5-10个关键词')
        self.fields['og_title_template'].help_text = _('社交媒体分享时显示的标题，不填则使用普通标题')
        self.fields['og_description_template'].help_text = _('社交媒体分享时显示的描述，不填则使用普通描述')
        self.fields['og_image'].help_text = _('社交媒体分享时显示的图片，建议尺寸1200x630像素') 