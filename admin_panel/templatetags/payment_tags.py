from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """获取字典中的值，如果不存在则返回空字符串"""
    if not dictionary:
        return ''
    return dictionary.get(key, '')

@register.filter
def currency_format(value, currency='USD'):
    """格式化货币显示"""
    if not value:
        return '0.00'
    
    try:
        value = float(value)
        currencies = {
            'CNY': '¥',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
        }
        symbol = currencies.get(currency, currency)
        return f"{symbol} {value:.2f}"
    except (ValueError, TypeError):
        return value

@register.filter
def json_pretty(value):
    """美化JSON显示"""
    if not value:
        return '{}'
    
    try:
        if isinstance(value, str):
            value = json.loads(value)
        formatted = json.dumps(value, indent=2, ensure_ascii=False)
        return mark_safe(f'<pre class="json-pretty">{formatted}</pre>')
    except Exception:
        return value 