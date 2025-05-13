from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from allauth.account.forms import SignupForm as AllauthSignupForm

from .models import FrontMenu, FrontUser, FrontGameComment, UserProfile

class FrontMenuForm(forms.ModelForm):
    """前台菜单表单"""
    
    class Meta:
        model = FrontMenu
        fields = ['name', 'url', 'icon', 'parent', 'order', 'is_active', 'is_external']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入菜单名称'}),
            'url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入菜单链接URL'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入图标类名，如 bi bi-house'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_external': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 设置父菜单选项，排除当前菜单及其子菜单
        if self.instance.pk:
            descendants_ids = [m.id for m in self.instance.get_descendants()]
            descendants_ids.append(self.instance.id)
            self.fields['parent'].queryset = FrontMenu.objects.exclude(id__in=descendants_ids)
        
        # 父菜单可以为空
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "-- 无父级菜单 --"
        
        # 图标字段非必填
        self.fields['icon'].required = False

class UserRegistrationForm(forms.ModelForm):
    """用户注册表单 - 使用Django默认User模型"""
    
    password = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'}),
        validators=[validate_password]
    )
    password_confirm = forms.CharField(
        label=_('确认密码'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入密码'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'})
        }
        
    def clean_password_confirm(self):
        """验证两次密码输入是否一致"""
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_('两次输入的密码不一致'))
        
        return password_confirm
        
    def clean_username(self):
        """验证用户名是否已被使用"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('该用户名已被使用'))
        return username
        
    def clean_email(self):
        """验证邮箱是否已被使用"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('该邮箱已被使用'))
        return email
        
    def save(self, commit=True):
        """保存用户信息，创建用户资料"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
            # 创建用户资料
            UserProfile.objects.create(user=user)
            
        return user

class GameCommentForm(forms.ModelForm):
    class Meta:
        model = FrontGameComment
        fields = ['rating', 'content']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入您的评价'})
        }

class ProfileUpdateForm(forms.ModelForm):
    """用户资料更新表单"""
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入个人简介'})
        }

class UserUpdateForm(forms.ModelForm):
    """用户账号信息更新表单"""
    
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }
        
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        super().__init__(*args, **kwargs)
        
    def clean_username(self):
        """验证用户名是否已被使用"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(id=self.user_id).exists():
            raise forms.ValidationError(_('该用户名已被使用'))
        return username
        
    def clean_email(self):
        """验证邮箱是否已被使用"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.user_id).exists():
            raise forms.ValidationError(_('该邮箱已被使用'))
        return email

class LoginForm(AuthenticationForm):
    """自定义登录表单，明确支持邮箱或用户名登录"""
    
    username = forms.CharField(
        label=_('邮箱或用户名'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入邮箱或用户名',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入密码'
        })
    )
    
    error_messages = {
        'invalid_login': _(
            "请输入正确的邮箱/用户名和密码。注意两者都区分大小写。"
        ),
        'inactive': _("此账号已被禁用。"),
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = '邮箱或用户名'

class CustomSignupForm(AllauthSignupForm):
    """
    自定义注册表单，增加同意用户协议选项和邮箱验证码
    """
    terms = forms.BooleanField(
        label=_("我已阅读并同意用户协议和隐私政策"),
        required=True,
        error_messages={
            'required': _("请阅读并同意用户协议和隐私政策")
        }
    )
    
    verification_code = forms.CharField(
        label=_("验证码"),
        required=True,
        max_length=6,
        min_length=6,
        error_messages={
            'required': _("请输入验证码"),
            'max_length': _("验证码长度错误"),
            'min_length': _("验证码长度错误")
        }
    )
    
    def clean(self):
        """验证表单数据"""
        from django.core.cache import cache
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        verification_code = cleaned_data.get('verification_code')
        
        if email and verification_code:
            # 验证验证码
            cache_key = f'register_verification_{email}'
            cached_data = cache.get(cache_key)
            
            if not cached_data:
                self.add_error('verification_code', _("验证码已过期，请重新获取"))
            elif cached_data['code'] != verification_code:
                self.add_error('verification_code', _("验证码错误"))
            elif cached_data['email'] != email:
                self.add_error('verification_code', _("验证码与邮箱不匹配"))
        
        return cleaned_data
    
    def save(self, request):
        """
        保存用户信息
        """
        from django.core.cache import cache
        
        # terms字段不是用户模型的一部分，在保存前需要弹出
        self.cleaned_data.pop('terms', None)
        
        # 验证码也不是用户模型的一部分
        verification_code = self.cleaned_data.pop('verification_code', None)
        email = self.cleaned_data.get('email')
        
        # 清除验证码缓存
        if email and verification_code:
            cache_key = f'register_verification_{email}'
            cache.delete(cache_key)
        
        return super().save(request) 