from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AdminPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_panel'
    verbose_name = _('后台管理')
    
    def ready(self):
        """应用就绪时注册信号"""
        # 导入信号处理器
        import admin_panel.signals 