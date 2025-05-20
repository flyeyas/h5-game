from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile
from .forms import UserRegistrationForm, UserLoginForm


class RegisterView(FormView):
    """用户注册视图"""
    template_name = 'games/auth/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('games:home')
    
    def form_valid(self, form):
        # 创建用户
        user = form.save()
        
        # 创建用户资料
        UserProfile.objects.create(user=user)
        
        # 自动登录
        login(self.request, user)
        
        messages.success(self.request, _('Registration successful. Welcome to HTML5 Games!'))
        return super().form_valid(form)


class LoginView(FormView):
    """用户登录视图"""
    template_name = 'games/auth/login.html'
    form_class = UserLoginForm
    success_url = reverse_lazy('games:home')
    
    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        # 验证用户
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(self.request, user)
            messages.success(self.request, _('Login successful. Welcome back!'))
            
            # 检查是否有next参数
            next_url = self.request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            return super().form_valid(form)
        else:
            messages.error(self.request, _('Invalid username or password.'))
            return self.form_invalid(form)


def logout_view(request):
    """用户登出视图"""
    logout(request)
    messages.success(request, _('You have been logged out successfully.'))
    return redirect('games:home')


class CustomPasswordResetView(PasswordResetView):
    """自定义密码重置视图"""
    template_name = 'games/auth/password_reset.html'
    email_template_name = 'games/auth/password_reset_email.html'
    success_url = reverse_lazy('games:password_reset_done')
    form_class = PasswordResetForm


class PasswordResetDoneView(TemplateView):
    """密码重置完成视图"""
    template_name = 'games/auth/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """自定义密码重置确认视图"""
    template_name = 'games/auth/password_reset_confirm.html'
    success_url = reverse_lazy('games:password_reset_complete')
    form_class = SetPasswordForm


class PasswordResetCompleteView(TemplateView):
    """密码重置完成视图"""
    template_name = 'games/auth/password_reset_complete.html'