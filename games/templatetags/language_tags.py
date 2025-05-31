from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def get_available_languages():
    """获取Django设置中的可用语言"""
    return settings.LANGUAGES

@register.simple_tag
def get_current_language_code():
    """获取当前语言代码"""
    from django.utils import translation
    return translation.get_language()