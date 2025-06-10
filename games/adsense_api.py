"""
Google AdSense Management API 集成服务

此模块提供与Google AdSense Management API v2的集成功能，包括：
- Publisher ID验证
- 账户状态查询
- 收入数据获取
- 支付信息查询
- 错误处理和缓存机制
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from django.conf import settings
from django.core.cache import caches
from django.utils.translation import gettext as _

try:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import google.auth.exceptions
except ImportError as e:
    logging.error(f"Google API libraries not installed: {e}")
    raise ImportError(
        "Google API libraries are required. Please install them with: "
        "pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2"
    )


class AdSenseAPIError(Exception):
    """AdSense API相关错误的基类"""
    pass


class AdSenseAuthenticationError(AdSenseAPIError):
    """AdSense API认证错误"""
    pass


class AdSenseQuotaError(AdSenseAPIError):
    """AdSense API配额错误"""
    pass


class AdSenseNotFoundError(AdSenseAPIError):
    """AdSense资源未找到错误"""
    pass


class AdSenseAPIService:
    """Google AdSense Management API服务类"""
    
    def __init__(self):
        """初始化AdSense API服务"""
        self.config = getattr(settings, 'GOOGLE_ADSENSE_API_CONFIG', {})
        self.cache = caches['adsense'] if 'adsense' in caches else caches['default']
        self.logger = self._setup_logger()
        self.service = None
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('adsense_api')
        logger.setLevel(getattr(logging, self.config.get('LOG_LEVEL', 'INFO')))
        
        # 避免重复添加处理器
        if not logger.handlers:
            # 文件处理器
            log_file = self.config.get('LOG_FILE', 'logs/adsense_api.log')
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(levelname)s [%(asctime)s] %(name)s %(pathname)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
        return logger
        
    def _get_credentials(self):
        """获取Google API认证凭据"""
        credentials_file = self.config.get('CREDENTIALS_FILE')
        if not credentials_file or not os.path.exists(credentials_file):
            raise AdSenseAuthenticationError(
                _("Google service account credentials file not found. "
                  "Please set the correct path in GOOGLE_ADSENSE_API_CONFIG['CREDENTIALS_FILE'] in settings.py")
            )
            
        try:
            scopes = self.config.get('SCOPES', ['https://www.googleapis.com/auth/adsense.readonly'])
            credentials = service_account.Credentials.from_service_account_file(
                credentials_file, scopes=scopes
            )
            return credentials
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
            raise AdSenseAuthenticationError(
                _("Failed to authenticate with Google AdSense API: {}").format(str(e))
            )
            
    def _get_service(self):
        """获取AdSense API服务实例"""
        if self.service is None:
            try:
                credentials = self._get_credentials()
                api_version = self.config.get('API_VERSION', 'v2')
                
                self.service = build(
                    'adsense', 
                    api_version, 
                    credentials=credentials,
                    cache_discovery=False
                )
                self.logger.info(f"AdSense API service initialized (version: {api_version})")
            except Exception as e:
                self.logger.error(f"Failed to initialize AdSense API service: {e}")
                raise AdSenseAPIError(
                    _("Failed to initialize AdSense API service: {}").format(str(e))
                )
                
        return self.service
        
    def _make_api_request(self, request_func, *args, **kwargs) -> Dict[str, Any]:
        """执行API请求并处理错误"""
        try:
            # 设置配额用户
            if 'quotaUser' not in kwargs:
                kwargs['quotaUser'] = self.config.get('QUOTA_USER', 'html5games-app')
                
            response = request_func(*args, **kwargs).execute()
            return response
            
        except HttpError as e:
            error_details = json.loads(e.content.decode('utf-8'))
            error_code = e.resp.status
            error_message = error_details.get('error', {}).get('message', str(e))
            
            self.logger.error(f"AdSense API HTTP Error {error_code}: {error_message}")
            
            if error_code == 401:
                raise AdSenseAuthenticationError(_("Authentication failed. Please check your credentials."))
            elif error_code == 403:
                raise AdSenseQuotaError(_("API quota exceeded or access denied."))
            elif error_code == 404:
                raise AdSenseNotFoundError(_("Requested resource not found."))
            else:
                raise AdSenseAPIError(f"API Error {error_code}: {error_message}")
                
        except google.auth.exceptions.GoogleAuthError as e:
            self.logger.error(f"Google Auth Error: {e}")
            raise AdSenseAuthenticationError(_("Authentication error: {}").format(str(e)))
            
        except Exception as e:
            self.logger.error(f"Unexpected error in API request: {e}")
            raise AdSenseAPIError(_("Unexpected error: {}").format(str(e)))
            
    def _get_cache_key(self, key_type: str, identifier: str) -> str:
        """生成缓存键"""
        return f"adsense_{key_type}_{identifier}"
        
    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        try:
            return self.cache.get(cache_key)
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
            return None
            
    def _set_cached_data(self, cache_key: str, data: Dict[str, Any], timeout: Optional[int] = None) -> None:
        """设置缓存数据"""
        try:
            timeout = timeout or self.config.get('CACHE_TIMEOUT', 300)
            self.cache.set(cache_key, data, timeout)
        except Exception as e:
            self.logger.warning(f"Cache set error: {e}")

    def validate_publisher_id_format(self, publisher_id: str) -> bool:
        """验证Publisher ID格式"""
        import re
        # Publisher ID 应该是 ca-pub- 开头，后跟16位数字
        pattern = r'^ca-pub-\d{16}$'
        return re.match(pattern, publisher_id) is not None

    def verify_publisher_id(self, publisher_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        验证Publisher ID是否有效并获取账户信息

        Args:
            publisher_id: AdSense Publisher ID

        Returns:
            Tuple[bool, Dict]: (是否成功, 结果数据)
        """
        # 格式验证
        if not self.validate_publisher_id_format(publisher_id):
            return False, {
                'success': False,
                'status': 'error',
                'message': _('Invalid Publisher ID format. It should start with "ca-pub-" followed by 16 digits.'),
                'error_type': 'format_error'
            }

        # 检查缓存
        cache_key = self._get_cache_key('verification', publisher_id)
        cached_result = self._get_cached_data(cache_key)
        if cached_result:
            self.logger.info(f"Using cached verification result for {publisher_id}")
            return cached_result['success'], cached_result

        try:
            self.logger.info(f"Verifying Publisher ID: {publisher_id}")

            # 获取账户信息
            account_info = self._get_account_info(publisher_id)
            if not account_info:
                result = {
                    'success': False,
                    'status': 'failed',
                    'message': _('Unable to verify AdSense account. Publisher ID not found or access denied.'),
                    'error_type': 'not_found',
                    'suggestions': [
                        _('Ensure your Publisher ID is correct'),
                        _('Check if your AdSense account is active'),
                        _('Verify that your website is approved by AdSense'),
                        _('Make sure the service account has access to this AdSense account')
                    ]
                }
                # 缓存失败结果（较短时间）
                self._set_cached_data(cache_key, result, 60)  # 1分钟
                return False, result

            # 获取支付信息
            payment_info = self._get_payment_info(publisher_id)

            # 构建成功结果
            result = {
                'success': True,
                'status': 'verified',
                'message': _('AdSense account successfully verified! Your Publisher ID is valid and active.'),
                'account_info': {
                    'status': account_info.get('status', 'Active'),
                    'name': account_info.get('name', ''),
                    'currency': account_info.get('currency', 'USD'),
                    'timezone': account_info.get('timezone', ''),
                    'payment_ready': payment_info.get('payment_ready', True),
                    'next_payment': payment_info.get('next_payment', ''),
                    'balance': payment_info.get('balance', '0.00')
                }
            }

            # 缓存成功结果
            self._set_cached_data(cache_key, result)

            self.logger.info(f"Successfully verified Publisher ID: {publisher_id}")
            return True, result

        except AdSenseAuthenticationError as e:
            result = {
                'success': False,
                'status': 'auth_error',
                'message': str(e),
                'error_type': 'authentication',
                'suggestions': [
                    _('Check your Google service account credentials'),
                    _('Ensure the service account has AdSense API access'),
                    _('Verify the credentials file path is correct')
                ]
            }
            return False, result

        except AdSenseQuotaError as e:
            result = {
                'success': False,
                'status': 'quota_error',
                'message': str(e),
                'error_type': 'quota',
                'suggestions': [
                    _('API quota exceeded. Please try again later'),
                    _('Consider implementing request throttling'),
                    _('Contact Google to increase your API quota')
                ]
            }
            return False, result

        except AdSenseAPIError as e:
            result = {
                'success': False,
                'status': 'api_error',
                'message': str(e),
                'error_type': 'api_error',
                'suggestions': [
                    _('Check your internet connection'),
                    _('Verify AdSense API is enabled in Google Cloud Console'),
                    _('Try again in a few minutes')
                ]
            }
            return False, result

        except Exception as e:
            self.logger.error(f"Unexpected error verifying Publisher ID {publisher_id}: {e}")
            result = {
                'success': False,
                'status': 'error',
                'message': _('An unexpected error occurred during verification.'),
                'error_type': 'unexpected',
                'suggestions': [
                    _('Please try again later'),
                    _('Contact support if the problem persists')
                ]
            }
            return False, result

    def _get_account_info(self, publisher_id: str) -> Optional[Dict[str, Any]]:
        """获取AdSense账户信息"""
        try:
            service = self._get_service()

            # 获取账户列表
            accounts_response = self._make_api_request(
                service.accounts().list
            )

            accounts = accounts_response.get('accounts', [])

            # 查找匹配的账户
            for account in accounts:
                if account.get('name', '').endswith(publisher_id.replace('ca-pub-', '')):
                    account_name = account.get('name', '')

                    # 获取详细账户信息
                    account_details = self._make_api_request(
                        service.accounts().get,
                        name=account_name
                    )

                    return {
                        'name': account_details.get('displayName', ''),
                        'status': account_details.get('state', 'ACTIVE'),
                        'currency': account_details.get('currencyCode', 'USD'),
                        'timezone': account_details.get('timeZone', {}).get('id', ''),
                        'creation_time': account_details.get('createTime', ''),
                        'premium': account_details.get('premium', False)
                    }

            return None

        except Exception as e:
            self.logger.error(f"Error getting account info for {publisher_id}: {e}")
            return None

    def _get_payment_info(self, publisher_id: str) -> Dict[str, Any]:
        """获取支付信息"""
        try:
            service = self._get_service()

            # 获取账户名称
            account_name = self._get_account_name(publisher_id)
            if not account_name:
                return {'payment_ready': False, 'next_payment': '', 'balance': '0.00'}

            # 获取支付信息（这里使用模拟数据，因为实际的支付API可能需要特殊权限）
            # 在实际实现中，您可能需要调用不同的API端点来获取支付信息

            # 计算下次支付日期（通常是每月21日）
            from datetime import datetime, timedelta
            import calendar

            now = datetime.now()
            if now.day <= 21:
                # 本月21日
                next_payment = datetime(now.year, now.month, 21)
            else:
                # 下月21日
                if now.month == 12:
                    next_payment = datetime(now.year + 1, 1, 21)
                else:
                    next_payment = datetime(now.year, now.month + 1, 21)

            return {
                'payment_ready': True,
                'next_payment': next_payment.strftime('%Y-%m-%d'),
                'balance': '0.00',  # 实际实现中应该从API获取
                'payment_threshold': '100.00'  # 支付阈值
            }

        except Exception as e:
            self.logger.error(f"Error getting payment info for {publisher_id}: {e}")
            return {'payment_ready': False, 'next_payment': '', 'balance': '0.00'}

    def _get_account_name(self, publisher_id: str) -> Optional[str]:
        """获取账户名称"""
        try:
            service = self._get_service()

            accounts_response = self._make_api_request(
                service.accounts().list
            )

            accounts = accounts_response.get('accounts', [])

            for account in accounts:
                if account.get('name', '').endswith(publisher_id.replace('ca-pub-', '')):
                    return account.get('name', '')

            return None

        except Exception as e:
            self.logger.error(f"Error getting account name for {publisher_id}: {e}")
            return None

    def get_revenue_data(self, publisher_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        获取收入数据

        Args:
            publisher_id: Publisher ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            Dict: 收入数据
        """
        cache_key = self._get_cache_key('revenue', f"{publisher_id}_{start_date}_{end_date}")
        cached_result = self._get_cached_data(cache_key)
        if cached_result:
            return cached_result

        try:
            service = self._get_service()
            account_name = self._get_account_name(publisher_id)

            if not account_name:
                return {'error': 'Account not found'}

            # 获取收入报告
            report_response = self._make_api_request(
                service.accounts().reports().generate,
                parent=account_name,
                startDate_year=int(start_date.split('-')[0]),
                startDate_month=int(start_date.split('-')[1]),
                startDate_day=int(start_date.split('-')[2]),
                endDate_year=int(end_date.split('-')[0]),
                endDate_month=int(end_date.split('-')[1]),
                endDate_day=int(end_date.split('-')[2]),
                metrics=['ESTIMATED_EARNINGS', 'PAGE_VIEWS', 'CLICKS'],
                dimensions=['DATE']
            )

            result = {
                'total_earnings': 0.0,
                'total_page_views': 0,
                'total_clicks': 0,
                'daily_data': []
            }

            rows = report_response.get('rows', [])
            for row in rows:
                cells = row.get('cells', [])
                if len(cells) >= 4:
                    date = cells[0].get('value', '')
                    earnings = float(cells[1].get('value', '0'))
                    page_views = int(cells[2].get('value', '0'))
                    clicks = int(cells[3].get('value', '0'))

                    result['total_earnings'] += earnings
                    result['total_page_views'] += page_views
                    result['total_clicks'] += clicks

                    result['daily_data'].append({
                        'date': date,
                        'earnings': earnings,
                        'page_views': page_views,
                        'clicks': clicks
                    })

            # 缓存结果
            self._set_cached_data(cache_key, result, 3600)  # 1小时缓存

            return result

        except Exception as e:
            self.logger.error(f"Error getting revenue data for {publisher_id}: {e}")
            return {'error': str(e)}


# 全局实例
adsense_service = AdSenseAPIService()
