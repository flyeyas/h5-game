from django import template

register = template.Library()

@register.filter
def findstr(value, arg):
    """
    在字符串中查找子字符串
    用法: {% if value|findstr:"search_text" %}
    """
    return arg in value

@register.filter
def get_item(dictionary, key):
    """
    从字典中获取指定键的值
    用法: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key) 