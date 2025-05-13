from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0023_merge_20250512_1349'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adminlog',
            old_name='created_at',
            new_name='timestamp',
        ),
        
        migrations.CreateModel(
            name='PayPalConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='配置名称')),
                ('description', models.TextField(blank=True, null=True, verbose_name='配置描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('receiver_email', models.EmailField(max_length=254, verbose_name='商户邮箱')),
                ('test_mode', models.BooleanField(default=True, verbose_name='测试模式')),
                ('return_url', models.CharField(max_length=255, verbose_name='支付成功跳转URL')),
                ('cancel_url', models.CharField(max_length=255, verbose_name='支付取消跳转URL')),
            ],
            options={
                'verbose_name': 'PayPal配置',
                'verbose_name_plural': 'PayPal配置',
            },
        ),
        migrations.CreateModel(
            name='MembershipPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='配置名称')),
                ('description', models.TextField(blank=True, null=True, verbose_name='配置描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('member_type', models.CharField(choices=[('1', '基础会员'), ('2', '高级会员'), ('3', 'VIP会员')], max_length=10, verbose_name='会员类型')),
                ('billing_cycle', models.CharField(choices=[('monthly', '月付'), ('yearly', '年付')], max_length=20, verbose_name='计费周期')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='价格')),
                ('currency', models.CharField(default='CNY', max_length=3, verbose_name='货币')),
                ('days', models.PositiveIntegerField(default=30, verbose_name='有效天数')),
            ],
            options={
                'verbose_name': '会员价格',
                'verbose_name_plural': '会员价格',
                'unique_together': {('member_type', 'billing_cycle')},
            },
        ),
    ] 