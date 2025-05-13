from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0002_frontend_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='frontendsession',
            name='user_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='用户ID'),
        ),
    ] 