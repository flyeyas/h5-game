from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0002_admin_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminsession',
            name='user_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='管理员ID'),
        ),
    ] 