from django import template
from games.models import FrontUser

register = template.Library()

@register.filter
def is_front_user(user):
    """
    检查用户是否为前台用户
    用法：{% if user|is_front_user %}
    """
    if not user or not user.is_authenticated:
        return False
        
    # 判断用户实例类型
    if isinstance(user, FrontUser):
        return True
        
    # 尝试查找对应的前台用户
    try:
        FrontUser.objects.get(username=user.username)
        return True
    except FrontUser.DoesNotExist:
        return False 