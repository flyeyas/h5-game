from .models import GameCategory, FrontMenu, FrontUser
import logging
from admin_panel.models import ConfigSettings

logger = logging.getLogger('games')

def game_categories(request):
    """提供游戏分类数据给所有页面"""
    categories = GameCategory.objects.filter(is_active=True, parent=None)
    return {'categories': categories}

def front_menu(request):
    """提供前台导航菜单数据给所有页面"""
    # 获取激活的顶级菜单
    main_menus = FrontMenu.objects.filter(is_active=True, parent=None).order_by('order', 'id')
    # 使用Manager方法获取菜单树（包含子菜单的结构）
    menu_tree = FrontMenu.objects.get_menu_tree()
    
    return {
        'front_menus': main_menus,
        'front_menu_tree': menu_tree
    }

def user_login_status(request):
    """
    提供用户登录状态信息给所有模板
    使用Django默认的用户认证系统
    """
    context = {
        'is_front_user': False,
        'front_user': None,
        'is_frontend_authenticated': False
    }
    
    if not request.user.is_authenticated:
        logger.debug("用户未登录")
        return context
    
    # 用户已登录，使用Django默认的User对象
    try:
        from .models import UserProfile
        
        # 获取用户资料
        try:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
        except Exception as e:
            logger.error(f"获取用户资料时出错: {str(e)}")
            profile = None
        
        # 记录日志
        user_id = getattr(request.user, 'id', None)
        username = getattr(request.user, 'username', 'unknown')
        session_key = getattr(request.session, 'session_key', None)
        
        logger.debug(f"用户登录状态: user_id={user_id}, username={username}, session_key={session_key}")
        
        # 返回状态信息 - 使用Django用户对象替代FrontUser
        context.update({
            'is_front_user': True,  # 这里设为True是为了保持向后兼容
            'front_user': request.user,  # 使用Django用户对象
            'is_frontend_authenticated': True,  # 用户已通过Django认证
            'front_user_id': request.user.id,
            'user_profile': profile
        })
        
    except Exception as e:
        logger.error(f"处理用户登录状态时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    return context 

def member_content_settings(request):
    """
    添加会员内容显示配置到模板上下文
    """
    # 从系统配置中获取会员内容显示配置，默认为True（显示）
    show_member_content = ConfigSettings.get_config('show_member_content', True)
    
    # 如果配置值是字符串的'false'或'0'，则认为是False
    if isinstance(show_member_content, str):
        show_member_content = show_member_content.lower() not in ('false', '0')
    
    return {
        'show_member_content': show_member_content,
    } 