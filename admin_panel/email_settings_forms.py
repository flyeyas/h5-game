from django import forms
from django.utils.translation import gettext_lazy as _

class EmailSettingsForm(forms.Form):
    """邮件设置表单"""
    # SMTP服务器设置
    enable_smtp = forms.BooleanField(
        label=_('启用SMTP邮件服务'),
        required=False,
    )
    
    smtp_server = forms.CharField(
        label=_('SMTP服务器'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('例如: smtp.example.com')}),
    )
    
    smtp_port = forms.IntegerField(
        label=_('SMTP端口'),
        required=False,
        min_value=1,
        max_value=65535,
        initial=25,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('默认: 25, SSL: 465, TLS: 587')}),
    )
    
    security_type = forms.ChoiceField(
        label=_('安全连接类型'),
        choices=[
            ('none', _('无加密')),
            ('ssl', 'SSL'),
            ('tls', 'TLS'),
        ],
        initial='none',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    
    require_authentication = forms.BooleanField(
        label=_('需要SMTP身份验证'),
        required=False,
    )
    
    smtp_username = forms.CharField(
        label=_('认证用户名'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('SMTP用户名')}),
    )
    
    smtp_password = forms.CharField(
        label=_('认证密码'),
        max_length=255,
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('SMTP密码')}),
    )
    
    # 邮件发送设置
    sender_email = forms.EmailField(
        label=_('发送邮箱'),
        max_length=255,
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('例如: service@yourdomain.com')}),
    )
    
    sender_name = forms.CharField(
        label=_('发送人名称'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('例如: GameHub服务团队')}),
    )
    
    send_timeout = forms.IntegerField(
        label=_('发送超时时间(秒)'),
        required=False,
        min_value=1,
        max_value=300,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('默认: 30秒')}),
    )
    
    # 测试邮件设置
    test_email = forms.EmailField(
        label=_('测试接收邮箱'),
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('输入接收测试邮件的邮箱地址')}),
    )
    
    def clean(self):
        """表单验证"""
        cleaned_data = super().clean()
        enable_smtp = cleaned_data.get('enable_smtp')
        
        # 如果启用了SMTP服务，验证必填字段
        if enable_smtp:
            smtp_server = cleaned_data.get('smtp_server')
            smtp_port = cleaned_data.get('smtp_port')
            sender_email = cleaned_data.get('sender_email')
            
            if not smtp_server:
                self.add_error('smtp_server', _('启用SMTP服务时，服务器地址不能为空'))
            
            if not smtp_port:
                self.add_error('smtp_port', _('启用SMTP服务时，端口不能为空'))
            
            if not sender_email:
                self.add_error('sender_email', _('启用SMTP服务时，发送邮箱不能为空'))
                
            # 如果需要认证，验证用户名和密码
            require_authentication = cleaned_data.get('require_authentication')
            if require_authentication:
                smtp_username = cleaned_data.get('smtp_username')
                smtp_password = cleaned_data.get('smtp_password')
                
                if not smtp_username:
                    self.add_error('smtp_username', _('启用SMTP认证时，用户名不能为空'))
                
                if not smtp_password:
                    self.add_error('smtp_password', _('启用SMTP认证时，密码不能为空'))
        
        return cleaned_data 