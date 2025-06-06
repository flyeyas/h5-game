from django import template
register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """添加CSS类到表单字段"""
    # 检查value是否有as_widget方法
    if hasattr(value, 'as_widget'):
        return value.as_widget(attrs={'class': arg})
    # 如果value是SafeString或其他不支持as_widget的对象，直接返回
    return value

@register.filter(name='attr')
def set_attr(field, attr_string):
    """设置表单字段的属性
    用法: {{ field|attr:"placeholder:Enter text" }}
    """
    if attr_string:
        key, val = attr_string.split(':')
        # 检查field是否有as_widget方法
        if hasattr(field, 'as_widget'):
            return field.as_widget(attrs={key: val})
        # 如果field是SafeString或其他不支持as_widget的对象，直接返回
        return field
    return field 