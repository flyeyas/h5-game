from django.utils import timezone
from django.db import models
from .models import Advertisement, Category
from django.conf import settings

def advertisements(request):
    """
    广告上下文处理器，提供广告内容
    """
    # 默认返回空字典
    ads = {
        'header_ads': [],
        'sidebar_ads': [],
        'game_between_ads': [],
        'footer_ads': []
    }
    
    current_time = timezone.now()
    
    # 获取所有活跃的广告
    active_ads = Advertisement.objects.filter(
        is_active=True
    ).filter(
        # 开始日期为空或者已经开始
        (models.Q(start_date__isnull=True) | models.Q(start_date__lte=current_time))
    ).filter(
        # 结束日期为空或者还未结束
        (models.Q(end_date__isnull=True) | models.Q(end_date__gte=current_time))
    )
    
    # 按位置分组广告
    for ad in active_ads:
        # 增加广告展示次数
        ad.view_count += 1
        ad.save(update_fields=['view_count'])
        
        if ad.position == 'header':
            ads['header_ads'].append(ad)
        elif ad.position == 'sidebar':
            ads['sidebar_ads'].append(ad)
        elif ad.position == 'game_between':
            ads['game_between_ads'].append(ad)
        elif ad.position == 'footer':
            ads['footer_ads'].append(ad)
    
    return ads

def website_settings(request):
    """添加网站设置到上下文"""
    # 提供导航菜单的分类数据
    categories = Category.objects.filter(parent=None, is_active=True)[:10]

    return {
        'categories': categories,
        'site_name': 'HTML5 Games',
        'site_description': 'Play the best free HTML5 games online',
    }