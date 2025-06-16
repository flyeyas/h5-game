from django.utils import timezone
from django.db import models
from .models import Advertisement, Category
from django.conf import settings

def advertisements(request):
    """
    Advertisement context processor that provides advertisement content
    """
    # Return empty dictionary by default
    ads = {
        'header_ads': [],
        'sidebar_ads': [],
        'game_between_ads': [],
        'footer_ads': []
    }
    
    current_time = timezone.now()

    # Get all active advertisements
    active_ads = Advertisement.objects.filter(
        is_active=True
    ).filter(
        # Start date is empty or has already started
        (models.Q(start_date__isnull=True) | models.Q(start_date__lte=current_time))
    ).filter(
        # End date is empty or has not ended yet
        (models.Q(end_date__isnull=True) | models.Q(end_date__gte=current_time))
    )

    # Group advertisements by position
    for ad in active_ads:
        # Increase advertisement view count
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
    """Add website settings to context"""
    # Provide category data for navigation menu
    categories = Category.objects.filter(parent=None, is_active=True)[:10]

    return {
        'categories': categories,
        'site_name': 'HTML5 Games',
        'site_description': 'Play the best free HTML5 games online',
    }