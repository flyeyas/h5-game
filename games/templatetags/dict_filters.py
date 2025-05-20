from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """从字典中获取键值"""
    return dictionary.get(key)

@register.filter
def get_nested_item(dictionary, key_path):
    """从嵌套字典中获取键值，使用点号分隔路径，如 'foo.bar.baz'"""
    keys = key_path.split('.')
    value = dictionary
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    
    return value 