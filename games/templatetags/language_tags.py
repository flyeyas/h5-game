from django import template
from django.core.cache import cache
from django.conf import settings
from games.models_menu_settings import Language

register = template.Library()

# 缓存超时时间（秒）
CACHE_TIMEOUT = 3600  # 1小时

@register.simple_tag
def get_active_languages():
    """获取所有激活的语言（带缓存）"""
    # 尝试从缓存获取
    languages = cache.get('active_languages')
    if languages is None:
        # 缓存未命中，从数据库获取
        languages = list(Language.objects.filter(is_active=True).order_by('name'))
        # 保存到缓存
        cache.set('active_languages', languages, CACHE_TIMEOUT)
    return languages

@register.simple_tag
def get_default_language():
    """获取默认语言（带缓存）"""
    # 尝试从缓存获取
    default_language = cache.get('default_language')
    if default_language is None:
        # 缓存未命中，从数据库获取
        default_language = Language.objects.filter(is_default=True).first()
        # 保存到缓存
        cache.set('default_language', default_language, CACHE_TIMEOUT)
    return default_language

@register.simple_tag
def get_language_by_code(code):
    """根据语言代码获取语言对象（带缓存）"""
    # 尝试从缓存获取
    cache_key = f'language_{code}'
    language = cache.get(cache_key)
    if language is None:
        # 缓存未命中，从数据库获取
        try:
            language = Language.objects.get(code=code)
            # 保存到缓存
            cache.set(cache_key, language, CACHE_TIMEOUT)
        except Language.DoesNotExist:
            return None
    return language 