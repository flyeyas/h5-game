from django import template

register = template.Library()

@register.filter
def getattribute(obj, attr):
    """从对象获取属性值"""
    return getattr(obj, attr, None)

@register.filter
def is_front_user(user):
    """判断用户是否为前台用户"""
    return user.__class__.__module__ == 'games.models' and user.__class__.__name__ == 'FrontUser' 

@register.filter
def rating_stars(game):
    """
    根据游戏评分返回星星列表
    返回格式: [1, 1, 1, 0.5, 0]  表示 3.5星
    1 表示满星，0.5 表示半星，0 表示空星
    """
    if not game or not hasattr(game, 'rating'):
        return [0, 0, 0, 0, 0]
    
    try:
        # 确保评分是浮点数
        rating = float(game.rating)
        stars = []
        
        # 计算满星、半星和空星
        for i in range(5):
            if rating >= i + 1:
                stars.append(1)  # 满星
            elif rating >= i + 0.5:
                stars.append(0.5)  # 半星
            else:
                stars.append(0)  # 空星
        
        return stars
    except (ValueError, TypeError):
        # 处理评分无效的情况
        return [0, 0, 0, 0, 0]

@register.filter
def range_num(value):
    """
    生成一个从1到指定数字的范围列表
    用于分页显示
    """
    try:
        value = int(value)
        return range(1, value + 1)
    except (ValueError, TypeError):
        return range(1, 1) 