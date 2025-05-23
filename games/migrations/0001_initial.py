# Generated by Django 5.2 on 2025-05-18 15:29

import cms.models.fields
import django.db.models.deletion
import filer.fields.image
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cms', '0042_alter_cmsplugin_id_alter_globalpagepermission_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.FILER_IMAGE_MODEL),
        migrations.swappable_dependency(settings.PLANS_PLAN_MODEL),
        migrations.swappable_dependency(settings.PLANS_USERPLAN_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='会员等级名称')),
                ('name_en', models.CharField(max_length=100, null=True, verbose_name='会员等级名称')),
                ('name_zh', models.CharField(max_length=100, null=True, verbose_name='会员等级名称')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='URL别名')),
                ('level', models.CharField(choices=[('free', '免费会员'), ('basic', '基础会员'), ('premium', '高级会员')], default='free', max_length=20, verbose_name='等级类型')),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='价格')),
                ('duration_days', models.PositiveIntegerField(default=30, verbose_name='有效期(天)')),
                ('description', models.TextField(verbose_name='会员权益描述')),
                ('description_en', models.TextField(null=True, verbose_name='会员权益描述')),
                ('description_zh', models.TextField(null=True, verbose_name='会员权益描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '会员等级',
                'verbose_name_plural': '会员等级',
                'ordering': ['price'],
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='支付方式名称')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='支付方式代码')),
                ('provider_class', models.CharField(max_length=255, verbose_name='提供商类')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                ('icon', models.FileField(blank=True, null=True, upload_to='payment_icons/', verbose_name='图标')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('configuration', models.JSONField(blank=True, default=dict, verbose_name='配置参数')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '支付方式',
                'verbose_name_plural': '支付方式',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Advertisement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='广告名称')),
                ('name_en', models.CharField(max_length=100, null=True, verbose_name='广告名称')),
                ('name_zh', models.CharField(max_length=100, null=True, verbose_name='广告名称')),
                ('position', models.CharField(choices=[('header', '页面顶部'), ('sidebar', '侧边栏'), ('game_between', '游戏间隙'), ('footer', '页面底部')], max_length=20, verbose_name='广告位置')),
                ('url', models.URLField(verbose_name='广告链接')),
                ('html_code', models.TextField(blank=True, help_text='如果使用第三方广告代码，请填写此字段', verbose_name='HTML代码')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name='开始日期')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='结束日期')),
                ('click_count', models.PositiveIntegerField(default=0, verbose_name='点击次数')),
                ('view_count', models.PositiveIntegerField(default=0, verbose_name='展示次数')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('image', filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ad_images', to=settings.FILER_IMAGE_MODEL, verbose_name='广告图片')),
            ],
            options={
                'verbose_name': '广告',
                'verbose_name_plural': '广告',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='分类名称')),
                ('name_en', models.CharField(max_length=100, null=True, verbose_name='分类名称')),
                ('name_zh', models.CharField(max_length=100, null=True, verbose_name='分类名称')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='URL别名')),
                ('description', models.TextField(blank=True, verbose_name='分类描述')),
                ('description_en', models.TextField(blank=True, null=True, verbose_name='分类描述')),
                ('description_zh', models.TextField(blank=True, null=True, verbose_name='分类描述')),
                ('order', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('image', filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='category_images', to=settings.FILER_IMAGE_MODEL, verbose_name='分类图片')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='games.category', verbose_name='父级分类')),
            ],
            options={
                'verbose_name': '游戏分类',
                'verbose_name_plural': '游戏分类',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='游戏标题')),
                ('title_en', models.CharField(max_length=200, null=True, verbose_name='游戏标题')),
                ('title_zh', models.CharField(max_length=200, null=True, verbose_name='游戏标题')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='URL别名')),
                ('description', models.TextField(verbose_name='游戏描述')),
                ('description_en', models.TextField(null=True, verbose_name='游戏描述')),
                ('description_zh', models.TextField(null=True, verbose_name='游戏描述')),
                ('iframe_url', models.URLField(verbose_name='游戏iframe链接')),
                ('is_featured', models.BooleanField(default=False, verbose_name='是否推荐')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
                ('rating', models.DecimalField(decimal_places=1, default=0.0, max_digits=3, verbose_name='评分')),
                ('view_count', models.PositiveIntegerField(default=0, verbose_name='浏览次数')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('categories', models.ManyToManyField(related_name='games', to='games.category', verbose_name='游戏分类')),
                ('content', cms.models.fields.PlaceholderField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, slotname='game_content', to='cms.placeholder', verbose_name='游戏内容')),
                ('thumbnail', filer.fields.image.FilerImageField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='game_thumbnails', to=settings.FILER_IMAGE_MODEL, verbose_name='游戏缩略图')),
            ],
            options={
                'verbose_name': '游戏',
                'verbose_name_plural': '游戏',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GameComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='评论内容')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=5, verbose_name='评分')),
                ('is_approved', models.BooleanField(default=True, verbose_name='是否审核通过')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='games.game', verbose_name='游戏')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_comments', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '游戏评论',
                'verbose_name_plural': '游戏评论',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True, verbose_name='Language Code')),
                ('name', models.CharField(max_length=100, verbose_name='Language Name')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('is_default', models.BooleanField(default=False, verbose_name='Default')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('flag', filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='language_flags', to=settings.FILER_IMAGE_MODEL, verbose_name='Flag')),
            ],
            options={
                'verbose_name': 'Language',
                'verbose_name_plural': 'Languages',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='MembershipPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('waiting', 'Waiting for confirmation'), ('preauth', 'Pre-authorized'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected'), ('refunded', 'Refunded'), ('error', 'Error'), ('input', 'Input')], default='waiting', max_length=10)),
                ('fraud_status', models.CharField(choices=[('unknown', 'Unknown'), ('accept', 'Passed'), ('reject', 'Rejected'), ('review', 'Review')], default='unknown', max_length=10, verbose_name='fraud check')),
                ('fraud_message', models.TextField(blank=True, default='')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('currency', models.CharField(max_length=10)),
                ('total', models.DecimalField(decimal_places=2, default='0.0', max_digits=9)),
                ('delivery', models.DecimalField(decimal_places=2, default='0.0', max_digits=9)),
                ('tax', models.DecimalField(decimal_places=2, default='0.0', max_digits=9)),
                ('description', models.TextField(blank=True, default='')),
                ('billing_first_name', models.CharField(blank=True, max_length=256)),
                ('billing_last_name', models.CharField(blank=True, max_length=256)),
                ('billing_address_1', models.CharField(blank=True, max_length=256)),
                ('billing_address_2', models.CharField(blank=True, max_length=256)),
                ('billing_city', models.CharField(blank=True, max_length=256)),
                ('billing_postcode', models.CharField(blank=True, max_length=256)),
                ('billing_country_code', models.CharField(blank=True, max_length=2)),
                ('billing_country_area', models.CharField(blank=True, max_length=256)),
                ('billing_email', models.EmailField(blank=True, max_length=254)),
                ('billing_phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None)),
                ('customer_ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('extra_data', models.TextField(blank=True, default='')),
                ('message', models.TextField(blank=True, default='')),
                ('token', models.CharField(blank=True, default='', max_length=36)),
                ('captured_amount', models.DecimalField(decimal_places=2, default='0.0', max_digits=9)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('transaction_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='交易ID')),
                ('is_recurring', models.BooleanField(default=False, verbose_name='是否为续费')),
                ('membership', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='games.membership', verbose_name='会员等级')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='membership_payments', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
                ('user_plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to=settings.PLANS_USERPLAN_MODEL, verbose_name='用户计划')),
            ],
            options={
                'verbose_name': '会员支付记录',
                'verbose_name_plural': '会员支付记录',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MembershipPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('membership', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='plan', to='games.membership', verbose_name='会员等级')),
                ('plan', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='membership_plan', to=settings.PLANS_PLAN_MODEL, verbose_name='订阅计划')),
            ],
            options={
                'verbose_name': '会员订阅计划',
                'verbose_name_plural': '会员订阅计划',
            },
        ),
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Menu Name')),
                ('name_en', models.CharField(max_length=100, null=True, verbose_name='Menu Name')),
                ('name_zh', models.CharField(max_length=100, null=True, verbose_name='Menu Name')),
                ('menu_type', models.CharField(choices=[('header', 'Header Menu'), ('footer', 'Footer Menu'), ('sidebar', 'Sidebar Menu'), ('backend', 'Backend Menu')], max_length=20, verbose_name='Menu Type')),
                ('order', models.IntegerField(default=0, verbose_name='Order')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Menu',
                'verbose_name_plural': 'Menus',
                'ordering': ['menu_type', 'order'],
                'unique_together': {('name', 'menu_type')},
            },
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('title_en', models.CharField(max_length=100, null=True, verbose_name='Title')),
                ('title_zh', models.CharField(max_length=100, null=True, verbose_name='Title')),
                ('url', models.CharField(max_length=200, verbose_name='URL')),
                ('icon', models.CharField(blank=True, help_text='Font Awesome icon class name', max_length=50, verbose_name='Icon')),
                ('target', models.CharField(choices=[('_self', 'Current Window'), ('_blank', 'New Window')], default='_self', max_length=10, verbose_name='Target')),
                ('order', models.IntegerField(default=0, verbose_name='Order')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('permission_required', models.CharField(blank=True, help_text='Django permission format, e.g.: app.add_model', max_length=100, verbose_name='Permission Required')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('menu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='games.menu', verbose_name='Menu')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='games.menuitem', verbose_name='Parent Item')),
            ],
            options={
                'verbose_name': 'Menu Item',
                'verbose_name_plural': 'Menu Items',
                'ordering': ['menu', 'order'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('membership_expiry', models.DateTimeField(blank=True, null=True, verbose_name='会员到期时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('avatar', filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_avatars', to=settings.FILER_IMAGE_MODEL, verbose_name='头像')),
                ('favorite_games', models.ManyToManyField(blank=True, related_name='favorited_by', to='games.game', verbose_name='收藏的游戏')),
                ('membership', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='games.membership', verbose_name='会员等级')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户资料',
                'verbose_name_plural': '用户资料',
            },
        ),
        migrations.CreateModel(
            name='WebsiteSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(max_length=100, verbose_name='Site Name')),
                ('site_name_en', models.CharField(max_length=100, null=True, verbose_name='Site Name')),
                ('site_name_zh', models.CharField(max_length=100, null=True, verbose_name='Site Name')),
                ('site_description', models.TextField(verbose_name='Site Description')),
                ('site_description_en', models.TextField(null=True, verbose_name='Site Description')),
                ('site_description_zh', models.TextField(null=True, verbose_name='Site Description')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Contact Email')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Contact Phone')),
                ('address', models.TextField(blank=True, verbose_name='Address')),
                ('copyright_text', models.CharField(blank=True, max_length=200, verbose_name='Copyright Text')),
                ('copyright_text_en', models.CharField(blank=True, max_length=200, null=True, verbose_name='Copyright Text')),
                ('copyright_text_zh', models.CharField(blank=True, max_length=200, null=True, verbose_name='Copyright Text')),
                ('facebook_url', models.URLField(blank=True, verbose_name='Facebook URL')),
                ('twitter_url', models.URLField(blank=True, verbose_name='Twitter URL')),
                ('instagram_url', models.URLField(blank=True, verbose_name='Instagram URL')),
                ('youtube_url', models.URLField(blank=True, verbose_name='YouTube URL')),
                ('meta_keywords', models.TextField(blank=True, help_text='SEO keywords separated by commas', verbose_name='Meta Keywords')),
                ('meta_keywords_en', models.TextField(blank=True, help_text='SEO keywords separated by commas', null=True, verbose_name='Meta Keywords')),
                ('meta_keywords_zh', models.TextField(blank=True, help_text='SEO keywords separated by commas', null=True, verbose_name='Meta Keywords')),
                ('meta_description', models.TextField(blank=True, help_text='SEO description', verbose_name='Meta Description')),
                ('meta_description_en', models.TextField(blank=True, help_text='SEO description', null=True, verbose_name='Meta Description')),
                ('meta_description_zh', models.TextField(blank=True, help_text='SEO description', null=True, verbose_name='Meta Description')),
                ('google_analytics_code', models.TextField(blank=True, verbose_name='Google Analytics Code')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('favicon', filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='site_favicons', to=settings.FILER_IMAGE_MODEL, verbose_name='Favicon')),
                ('logo', filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='site_logos', to=settings.FILER_IMAGE_MODEL, verbose_name='Site Logo')),
            ],
            options={
                'verbose_name': 'Website Setting',
                'verbose_name_plural': 'Website Settings',
            },
        ),
        migrations.CreateModel(
            name='GameHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('play_time', models.PositiveIntegerField(default=0, verbose_name='游戏时长(秒)')),
                ('played_at', models.DateTimeField(auto_now_add=True, verbose_name='游玩时间')),
                ('last_played', models.DateTimeField(auto_now=True, verbose_name='最后游戏时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='play_history', to='games.game', verbose_name='游戏')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_history', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '游戏历史',
                'verbose_name_plural': '游戏历史',
                'ordering': ['-last_played'],
                'unique_together': {('user', 'game')},
            },
        ),
    ]
