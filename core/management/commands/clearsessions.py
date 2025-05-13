from django.core.management.base import BaseCommand
from django.utils import timezone
from games.sessions import FrontendSession
from admin_panel.sessions import AdminSession
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '清理已过期的前台和后台会话记录'

    def handle(self, *args, **options):
        """
        执行清理会话的命令
        """
        # 当前时间
        now = timezone.now()
        
        # 清理前台会话
        frontend_expired = FrontendSession.objects.filter(expire_date__lt=now)
        frontend_count = frontend_expired.count()
        frontend_expired.delete()
        
        # 清理后台会话
        admin_expired = AdminSession.objects.filter(expire_date__lt=now)
        admin_count = admin_expired.count()
        admin_expired.delete()
        
        # 输出结果
        self.stdout.write(
            self.style.SUCCESS(f'成功清理 {frontend_count} 条前台过期会话和 {admin_count} 条后台过期会话')
        )
        
        # 记录日志
        logger.info(f'清理会话: 删除了 {frontend_count} 条前台过期会话和 {admin_count} 条后台过期会话')
        
        return None 