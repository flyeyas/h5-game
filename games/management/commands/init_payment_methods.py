from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from games.models_payment import PaymentMethod
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize payment methods'

    def handle(self, *args, **options):
        self.stdout.write('Creating default payment methods...')
        
        # 创建全局配置
        global_config, created = PaymentMethod.objects.update_or_create(
            code='global_config',
            defaults={
                'name': 'Global Payment Configuration',
                'provider_class': 'payments.dummy.DummyProvider',
                'is_active': True,
                'sort_order': 999,
                'description': 'Global payment security and configuration settings.',
                'configuration': {
                    'security_key': 'default-key-replace-in-database',
                    'security_salt': 'default-salt-replace-in-database',
                    'fraud_threshold': 3,
                    'currency': 'USD',
                    'tax': 0,
                    'payment_host': 'localhost:8000',
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created global payment configuration'))
        else:
            self.stdout.write(self.style.WARNING('Updated global payment configuration'))
        
        # 定义默认支付方法
        default_methods = [
            {
                'name': 'Dummy Payment (Testing)',
                'code': 'dummy',
                'provider_class': 'payments.dummy.DummyProvider',
                'is_active': True,
                'sort_order': 100,
                'description': 'For testing purposes only. No real payments are processed.',
                'configuration': {
                    'auto_confirm': True
                }
            },
            {
                'name': 'PayPal',
                'code': 'paypal',
                'provider_class': 'payments.paypal.PaypalProvider',
                'is_active': True,
                'sort_order': 1,
                'description': 'Pay securely with PayPal',
                'configuration': {
                    'client_id': '',
                    'secret': '',
                    'endpoint': 'https://api.sandbox.paypal.com',
                    'capture': True
                }
            },
            {
                'name': 'Stripe',
                'code': 'stripe',
                'provider_class': 'payments.stripe.StripeProvider',
                'is_active': True,
                'sort_order': 2,
                'description': 'Pay with credit or debit card via Stripe',
                'configuration': {
                    'api_key': '',
                    'public_key': ''
                }
            },
            {
                'name': 'Bank Transfer',
                'code': 'bank_transfer',
                'provider_class': 'payments.manual.ManualProvider',
                'is_active': True,
                'sort_order': 3,
                'description': 'Pay via bank transfer',
                'configuration': {
                    'instructions': 'Please transfer the payment to our bank account and provide the reference number.',
                    'account_details': 'Bank: Example Bank, Account: 1234567890, Name: Company Ltd',
                    'requires_admin_confirmation': True
                }
            }
        ]
        
        # 创建支付方法
        created_count = 0
        updated_count = 0
        for method_data in default_methods:
            code = method_data.pop('code')
            configuration = method_data.pop('configuration')
            
            # 尝试查找现有支付方法
            payment_method, created = PaymentMethod.objects.update_or_create(
                code=code,
                defaults={
                    **method_data,
                    'configuration': configuration
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created payment method: {payment_method.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated payment method: {payment_method.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} and updated {updated_count} payment methods.')) 