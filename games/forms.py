from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True, label=_('Email'))
    first_name = forms.CharField(max_length=30, required=False, label=_('First Name'))
    last_name = forms.CharField(max_length=30, required=False, label=_('Last Name'))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap类
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        
        return user


class UserLoginForm(forms.Form):
    """用户登录表单"""
    username = forms.CharField(max_length=150, label=_('Username'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    remember_me = forms.BooleanField(required=False, label=_('Remember Me'))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap类
        for field_name, field in self.fields.items():
            if field_name != 'remember_me':
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label
            else:
                field.widget.attrs['class'] = 'form-check-input'


class UserProfileForm(forms.ModelForm):
    """用户资料表单"""
    first_name = forms.CharField(max_length=30, required=False, label=_('First Name'))
    last_name = forms.CharField(max_length=30, required=False, label=_('Last Name'))
    email = forms.EmailField(required=True, label=_('Email'))
    
    class Meta:
        model = UserProfile
        fields = ('avatar',)
        labels = {
            'avatar': _('Profile Picture'),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
        
        # 添加Bootstrap类
        for field_name, field in self.fields.items():
            if field_name != 'avatar':
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control-file'
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            self.user.save()
        
        if commit:
            profile.save()
        
        return profile