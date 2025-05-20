from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Advertisement

@require_POST
@csrf_exempt
def ad_click(request, ad_id):
    """
    记录广告点击
    """
    try:
        ad = Advertisement.objects.get(id=ad_id)
        ad.click_count += 1
        ad.save(update_fields=['click_count'])
        return JsonResponse({'status': 'success'})
    except Advertisement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Advertisement not found'}, status=404)