from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GamesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'games'
    verbose_name = _('游戏管理')
    
    def ready(self):
        import games.signals