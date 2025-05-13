from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from .admin_user import AdminUser
from .menu import Menu

class MenuForm(forms.ModelForm):
    """菜单表单"""
    class Meta:
        model = Menu
        fields = ['name', 'url', 'icon', 'parent', 'order', 'is_active']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'placeholder': 'fas fa-home'}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 排除当前菜单及其子菜单，防止循环引用
        if self.instance.pk:
            self.fields['parent'].queryset = Menu.objects.exclude(
                pk__in=[self.instance.pk] + [c.pk for c in self.instance.children.all()]
            )
        # 添加空选项
        self.fields['parent'].empty_label = _('无 (作为顶级菜单)')

class AdminUserForm(forms.ModelForm):
    """管理员用户表单"""
    password = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(),
        required=False,
        help_text=_('如果不修改密码，请留空')
    )
    confirm_password = forms.CharField(
        label=_('确认密码'),
        widget=forms.PasswordInput(),
        required=False
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        widgets = {
            'is_active': forms.CheckboxInput(),
            'is_staff': forms.CheckboxInput(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # 如果设置了密码，则需要验证两次输入是否一致
        if password:
            if password != confirm_password:
                self.add_error('confirm_password', _('两次输入的密码不一致'))
        
        return cleaned_data