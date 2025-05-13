from django import template
from django.middleware.csrf import get_token
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def app_csrf_token(context):
    """返回标准的CSRF令牌"""
    request = context['request']
    return mark_safe(f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">')

@register.simple_tag(takes_context=True)
def get_csrf_header_name(context):
    """获取标准的CSRF头名称，转换为HTTP格式"""
    return 'X-CSRFToken'

@register.simple_tag(takes_context=True)
def get_csrf_cookie_name(context):
    """获取标准的CSRF Cookie名称"""
    return 'csrftoken' 