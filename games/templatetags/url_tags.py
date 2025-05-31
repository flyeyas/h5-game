from django import template

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    """
    Template tag to replace a parameter in the current URL query string
    
    Usage:
    <a href="?{% url_replace request 'page' 2 %}">Page 2</a>
    """
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()