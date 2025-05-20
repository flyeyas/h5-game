from celery import Celery
from celery.schedules import crontab
from django.conf import settings

app = Celery('html5games')

# 使用Django的设置文件配置Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# 配置定时任务
app.conf.beat_schedule = {
    'check-payment-timeouts': {
        'task': 'games.tasks.check_payment_timeouts',
        'schedule': crontab(minute='*/5'),  # 每5分钟执行一次
    },
    'process-payment-notifications': {
        'task': 'games.tasks.process_payment_notifications',
        'schedule': crontab(minute='*/1'),  # 每分钟执行一次
    },
} 