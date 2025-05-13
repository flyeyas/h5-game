from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class MenuManager(models.Manager):
    """
    菜单管理器，提供菜单相关的查询方法
    """
    def get_active_menus(self):
        """
        获取所有启用的菜单
        """
        return self.filter(is_active=True).order_by('order', 'id')
    
    def get_menu_tree(self):
        """
        获取菜单树结构
        """
        # 获取所有启用的菜单
        all_menus = self.get_active_menus()
        
        # 构建菜单树
        menu_tree = []
        menu_dict = {menu.id: menu for menu in all_menus}
        
        # 添加顶级菜单
        for menu in all_menus:
            if menu.parent is None:
                menu_tree.append(menu)
        
        return menu_tree

class Menu(models.Model):
    """
    菜单模型 - 用于管理后台导航菜单
    """
    name = models.CharField(_('菜单名称'), max_length=50)
    url = models.CharField(_('链接URL'), max_length=200)
    icon = models.CharField(_('图标'), max_length=50, blank=True, help_text=_('FontAwesome图标类名，例如：fas fa-home'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name=_('父级菜单'))
    order = models.IntegerField(_('排序'), default=0, help_text=_('数字越小排序越靠前'))
    is_active = models.BooleanField(_('是否启用'), default=True)
    created_time = models.DateTimeField(_('创建时间'), default=timezone.now)
    updated_time = models.DateTimeField(_('更新时间'), auto_now=True)
    
    # 使用自定义管理器
    objects = MenuManager()
    
    class Meta:
        verbose_name = _('菜单')
        verbose_name_plural = _('菜单列表')
        ordering = ['order', 'id']
    
    def __str__(self):
        return self.name
    
    @property
    def level(self):
        """
        获取菜单层级
        """
        level = 0
        p = self.parent
        while p is not None:
            level += 1
            p = p.parent
        return level
    
    def get_children(self):
        """
        获取子菜单
        """
        return self.children.filter(is_active=True).order_by('order')
    
    def has_children(self):
        """
        判断是否有子菜单
        """
        return self.children.filter(is_active=True).exists()
    
    def get_ancestors(self):
        """
        获取所有祖先菜单
        """
        ancestors = []
        p = self.parent
        while p is not None:
            ancestors.append(p)
            p = p.parent
        return ancestors[::-1]  # 反转，从根到叶
    
    def get_descendants(self):
        """
        获取所有后代菜单
        """
        descendants = []
        
        def _get_descendants(menu):
            for child in menu.children.all():
                descendants.append(child)
                _get_descendants(child)
        
        _get_descendants(self)
        return descendants