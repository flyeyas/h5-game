from django.conf import settings
from django.apps import apps
from django.core.cache import cache
import logging

logger = logging.getLogger('payment_process')

def get_provider_from_db(variant, payment=None):
    """
    从数据库获取支付提供商配置，替代django-payments默认的provider_factory
    
    参数:
        variant: 支付方式代码，对应PaymentMethod.code
        payment: 支付记录实例
    
    返回:
        支付提供商实例
    """
    try:
        # 延迟导入，避免循环依赖
        from games.models_payment import PaymentMethod
        
        # 从缓存中获取支付方式配置
        cache_key = f'payment_method_{variant}'
        payment_method = cache.get(cache_key)
        
        if not payment_method:
            # 从数据库获取支付方式
            payment_method = PaymentMethod.objects.get(code=variant, is_active=True)
            # 缓存配置，减少数据库查询
            cache.set(cache_key, payment_method, 3600)
        
        # 获取提供商实例
        provider_instance = payment_method.get_provider_instance(payment)
        
        if provider_instance:
            return provider_instance
    except Exception as e:
        logger.error(f"Error getting provider from database: {str(e)}", exc_info=True)
    
    # 回退到settings中的默认配置
    logger.warning(f"Falling back to default provider for variant: {variant}")
    return _fallback_provider_factory(variant, payment)

def _fallback_provider_factory(variant, payment=None):
    """
    当数据库配置不可用时，回退到django-payments默认的provider_factory实现
    """
    from payments import provider_factory as payments_provider_factory
    
    # 设置一个最小的PAYMENTS_VARIANTS配置，确保默认提供商可用
    if not hasattr(settings, 'PAYMENTS_VARIANTS') or variant not in settings.PAYMENTS_VARIANTS:
        settings.PAYMENTS_VARIANTS = getattr(settings, 'PAYMENTS_VARIANTS', {})
        if variant not in settings.PAYMENTS_VARIANTS:
            settings.PAYMENTS_VARIANTS[variant] = ('payments.dummy.DummyProvider', {})
    
    return payments_provider_factory(variant, payment)

# 提供一个别名，保持与原始django-payments API兼容
provider_factory = get_provider_from_db 