from django.db.models.signals import post_migrate, post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from .models_menu_settings import Language

def sync_languages_with_settings():
    """同步数据库中的语言设置到Django设置"""
    from .views_menu_settings import update_django_languages
    
    # 确保至少有一种语言
    if not Language.objects.exists():
        # 初始化默认支持的语言
        for code, name in [('en', 'English'), ('zh', '中文')]:
            Language.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'is_active': True,
                    'is_default': code == 'en'  # 英语作为默认语言
                }
            )
    
    # 更新Django语言设置
    update_django_languages()
    
    # 清除语言相关的缓存
    clear_language_cache()

def clear_language_cache():
    """清除所有语言相关缓存"""
    cache.delete('active_languages')
    cache.delete('default_language')
    
    # 清除每个语言的缓存
    for language in Language.objects.all():
        cache.delete(f'language_{language.code}')

@receiver(post_migrate)
def initialize_languages(sender, **kwargs):
    """在迁移完成后初始化语言"""
    if sender.name == 'games':
        sync_languages_with_settings()

@receiver(post_save, sender=Language)
def language_saved(sender, instance, **kwargs):
    """当Language被保存时更新设置并清除缓存"""
    from .views_menu_settings import update_django_languages
    update_django_languages()
    clear_language_cache()

@receiver(post_delete, sender=Language)
def language_deleted(sender, instance, **kwargs):
    """当Language被删除时更新设置并清除缓存"""
    from .views_menu_settings import update_django_languages
    update_django_languages()
    clear_language_cache() 