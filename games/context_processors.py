from django.utils import timezone
from django.db import models
from .models import Advertisement, UserProfile
from django.conf import settings
from .models_menu_settings import WebsiteSetting, Language

def advertisements(request):
    """
    广告上下文处理器，根据用户会员状态和广告位置提供广告内容
    """
    # 默认返回空字典
    ads = {
        'header_ads': [],
        'sidebar_ads': [],
        'game_between_ads': [],
        'footer_ads': []
    }
    
    # 检查用户是否是会员，会员用户不显示广告
    is_premium_user = False
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.membership and profile.membership_expiry and profile.membership_expiry > timezone.now():
                if profile.membership.level in ['basic', 'premium']:
                    is_premium_user = True
        except UserProfile.DoesNotExist:
            pass
    
    # 如果不是会员用户，则加载广告
    if not is_premium_user:
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
    try:
        website_settings = WebsiteSetting.get_settings()
        show_language_switcher = getattr(website_settings, 'enable_language_switcher', True)
        auto_detect_language = getattr(website_settings, 'auto_detect_language', False)
        default_language = Language.objects.filter(is_default=True).first()
        active_languages = Language.objects.filter(is_active=True)
        
        return {
            'site_name': website_settings.site_name,
            'site_description': website_settings.site_description,
            'site_logo': website_settings.logo,
            'site_favicon': website_settings.favicon,
            'copyright_text': website_settings.copyright_text,
            'social_links': {
                'facebook': website_settings.facebook_url,
                'twitter': website_settings.twitter_url,
                'instagram': website_settings.instagram_url,
                'youtube': website_settings.youtube_url,
            },
            'contact_info': {
                'email': website_settings.email,
                'phone': website_settings.phone,
                'address': website_settings.address,
            },
            'language_settings': {
                'show_switcher': show_language_switcher,
                'auto_detect': auto_detect_language,
                'default': default_language.code if default_language else settings.LANGUAGE_CODE,
            },
            'active_languages': active_languages,
        }
    except (WebsiteSetting.DoesNotExist, AttributeError):
        return {}