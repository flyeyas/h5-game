from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from .models import Advertisement
import json

@require_POST
@csrf_exempt
def ad_click(request, ad_id):
    """
    记录广告点击
    """
    try:
        ad = Advertisement.objects.get(id=ad_id)
        ad.click_count += 1
        ad.calculate_ctr()
        ad.save(update_fields=['click_count', 'ctr'])
        return JsonResponse({'status': 'success'})
    except Advertisement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Advertisement not found'}, status=404)

@require_POST
@csrf_exempt
def ad_view(request, ad_id):
    """
    记录广告展示
    """
    try:
        ad = Advertisement.objects.get(id=ad_id)
        ad.view_count += 1
        ad.calculate_ctr()
        ad.save(update_fields=['view_count', 'ctr'])
        return JsonResponse({'status': 'success'})
    except Advertisement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Advertisement not found'}, status=404)

@require_GET
def ad_statistics(request):
    """
    获取广告统计数据
    """
    try:
        # 获取活跃广告数量
        active_ads = Advertisement.objects.filter(is_active=True).count()

        # 获取总统计数据
        total_stats = Advertisement.objects.aggregate(
            total_views=Sum('view_count'),
            total_clicks=Sum('click_count'),
            total_revenue=Sum('revenue'),
            avg_ctr=Avg('ctr')
        )

        # 获取本月数据（这里简化处理，实际应该根据时间范围过滤）
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 按位置统计
        position_stats = []
        for position_code, position_name in Advertisement.POSITION_CHOICES:
            ads_in_position = Advertisement.objects.filter(position=position_code, is_active=True)
            stats = ads_in_position.aggregate(
                count=Count('id'),
                views=Sum('view_count'),
                clicks=Sum('click_count'),
                revenue=Sum('revenue')
            )
            position_stats.append({
                'position': position_code,
                'position_name': str(position_name),
                'count': stats['count'] or 0,
                'views': stats['views'] or 0,
                'clicks': stats['clicks'] or 0,
                'revenue': float(stats['revenue'] or 0)
            })

        return JsonResponse({
            'status': 'success',
            'data': {
                'active_ads': active_ads,
                'total_views': total_stats['total_views'] or 0,
                'total_clicks': total_stats['total_clicks'] or 0,
                'total_revenue': float(total_stats['total_revenue'] or 0),
                'avg_ctr': float(total_stats['avg_ctr'] or 0),
                'position_stats': position_stats
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_GET
def revenue_reports(request):
    """
    获取Revenue Reports数据，支持时间段筛选
    """
    try:
        # 获取时间段参数
        period = request.GET.get('period', 'today')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        # 计算时间范围
        now = timezone.now()

        # 如果提供了自定义日期范围
        if start_date_str and end_date_str:
            try:
                from datetime import datetime
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
                # 转换为timezone-aware datetime
                start_date = timezone.make_aware(start_date)
                end_date = timezone.make_aware(end_date)
                period = 'custom'
            except ValueError:
                # 如果日期格式错误，回退到默认
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                period = 'today'
        elif period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'yesterday':
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'this_week':
            # 本周开始（周一）
            days_since_monday = now.weekday()
            start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'this_month':
            # 本月开始
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        else:
            # 默认为今天
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        # 由于我们的模型没有时间戳字段来过滤广告数据，我们需要模拟一些数据
        # 在实际项目中，您需要添加一个AdStatistics模型来记录每日的统计数据

        # 模拟不同时间段的数据
        mock_data = {
            'today': {
                'revenue': 45.67,
                'views': 1234,
                'clicks': 89,
                'ctr': 7.2,
                'change': '+12.5%'
            },
            'yesterday': {
                'revenue': 52.34,
                'views': 1456,
                'clicks': 102,
                'ctr': 7.0,
                'change': '+8.3%'
            },
            'this_week': {
                'revenue': 342.18,
                'views': 8765,
                'clicks': 567,
                'ctr': 6.5,
                'change': '+15.2%'
            },
            'this_month': {
                'revenue': 2913.97,
                'views': 718800,
                'clicks': 21400,
                'ctr': 3.3,
                'change': '+22.1%'
            },
            'custom': {
                'revenue': 0,
                'views': 0,
                'clicks': 0,
                'ctr': 0,
                'change': '0%'
            }
        }

        # 获取对应时间段的数据
        data = mock_data.get(period, mock_data['today'])

        # 如果是自定义日期范围，根据日期范围计算模拟数据
        if period == 'custom' and start_date and end_date:
            days_diff = (end_date.date() - start_date.date()).days + 1
            # 基于天数计算模拟数据
            daily_avg_revenue = 45.67
            daily_avg_views = 1234
            daily_avg_clicks = 89

            data = {
                'revenue': round(daily_avg_revenue * days_diff, 2),
                'views': int(daily_avg_views * days_diff),
                'clicks': int(daily_avg_clicks * days_diff),
                'ctr': round((daily_avg_clicks * days_diff) / (daily_avg_views * days_diff) * 100, 1),
                'change': f'+{round(days_diff * 2.5, 1)}%'
            }

        # 在实际项目中，这里应该是真实的数据库查询
        # 例如：
        # ads_in_period = Advertisement.objects.filter(
        #     created_at__gte=start_date,
        #     created_at__lte=end_date,
        #     is_active=True
        # )
        # stats = ads_in_period.aggregate(
        #     total_views=Sum('view_count'),
        #     total_clicks=Sum('click_count'),
        #     total_revenue=Sum('revenue'),
        #     avg_ctr=Avg('ctr')
        # )

        return JsonResponse({
            'status': 'success',
            'data': {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'revenue': data['revenue'],
                'views': data['views'],
                'clicks': data['clicks'],
                'ctr': data['ctr'],
                'change': data['change']
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
def toggle_ad_status(request, ad_id):
    """
    切换广告状态
    """
    try:
        ad = Advertisement.objects.get(id=ad_id)
        data = json.loads(request.body)
        ad.is_active = data.get('is_active', not ad.is_active)
        ad.save(update_fields=['is_active'])

        return JsonResponse({
            'success': True,
            'message': 'Advertisement status updated successfully',
            'is_active': ad.is_active
        })
    except Advertisement.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Advertisement not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_POST
@staff_member_required
def edit_ad_ajax(request, ad_id):
    """
    通过AJAX编辑广告单元
    """
    try:
        ad = Advertisement.objects.get(id=ad_id)

        # 更新广告数据
        ad.name = request.POST.get('name', ad.name)
        ad.adsense_unit_id = request.POST.get('adsense_unit_id', ad.adsense_unit_id)
        ad.ad_type = request.POST.get('ad_type', ad.ad_type)
        ad.ad_size = request.POST.get('ad_size', ad.ad_size)
        ad.position = request.POST.get('position', ad.position)
        ad.is_active = request.POST.get('is_active') == '1'
        ad.url = request.POST.get('url', ad.url)
        ad.html_code = request.POST.get('html_code', ad.html_code)

        # 保存更改
        ad.save()

        return JsonResponse({
            'success': True,
            'message': 'Ad unit updated successfully',
            'data': {
                'id': ad.id,
                'name': ad.name,
                'adsense_unit_id': ad.adsense_unit_id,
                'ad_type': ad.ad_type,
                'ad_size': ad.ad_size,
                'position': ad.position,
                'is_active': ad.is_active,
                'url': ad.url,
                'html_code': ad.html_code,
                'view_count': ad.view_count,
                'click_count': ad.click_count,
                'ctr': ad.ctr,
                'revenue': float(ad.revenue)
            }
        })
    except Advertisement.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Advertisement not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)