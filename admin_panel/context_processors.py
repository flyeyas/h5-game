from django.utils.translation import gettext_lazy as _
from .menu import Menu
from .site_settings import SiteSettings
from django.urls import reverse

def admin_menu(request):
    """自定义上下文处理器，添加管理菜单到模板上下文"""
    if request.user.is_authenticated and request.user.is_staff:
        # 获取菜单树
        menu_tree = Menu.objects.get_menu_tree()
        
        # 获取网站设置
        site_settings = SiteSettings.get_settings()
        
        return {
            'menu_tree': menu_tree,
            'site_settings': site_settings,
        }
    return {'menu_tree': None, 'site_settings': None}