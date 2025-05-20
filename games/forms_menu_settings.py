from django import forms
from django.utils.translation import gettext_lazy as _
from .models_menu_settings import Menu, MenuItem, WebsiteSetting


class MenuForm(forms.ModelForm):
    """菜单表单"""
    class Meta:
        model = Menu
        fields = ['name', 'menu_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'menu_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MenuItemForm(forms.ModelForm):
    """菜单项表单"""
    class Meta:
        model = MenuItem
        fields = ['title', 'url', 'icon', 'target', 'parent', 'order', 'is_active', 'permission_required']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'target': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permission_required': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        menu = kwargs.pop('menu', None)
        super().__init__(*args, **kwargs)
        
        if menu:
            # 只显示当前菜单的菜单项作为父级选项
            self.fields['parent'].queryset = MenuItem.objects.filter(menu=menu)
            # 如果是编辑现有菜单项，从父级选项中排除自己及其子项
            if self.instance.pk:
                descendants = []
                # 获取所有子项
                def get_descendants(item):
                    children = MenuItem.objects.filter(parent=item)
                    for child in children:
                        descendants.append(child.pk)
                        get_descendants(child)
                
                get_descendants(self.instance)
                # 排除自己和所有子项
                if descendants:
                    self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
                        pk__in=[self.instance.pk] + descendants
                    )


class WebsiteSettingForm(forms.ModelForm):
    """网站设置表单"""
    class Meta:
        model = WebsiteSetting
        fields = [
            'site_name', 'site_description', 'logo', 'favicon',
            'email', 'phone', 'address', 'copyright_text',
            'facebook_url', 'twitter_url', 'instagram_url', 'youtube_url',
            'meta_keywords', 'meta_description', 'google_analytics_code'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control'}),
            'meta_keywords': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'google_analytics_code': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }