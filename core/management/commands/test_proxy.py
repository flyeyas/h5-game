"""
测试代理连接的命令行工具
"""

import requests
import time
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from core.utils.proxy import get_proxy_from_env

class Command(BaseCommand):
    help = '测试代理连接到Google服务的可用性'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            default='https://oauth2.googleapis.com/token',
            help='要测试连接的URL，默认为Google OAuth2服务'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=10,
            help='请求超时时间（秒）'
        )
        parser.add_argument(
            '--disable-proxy',
            action='store_true',
            help='禁用代理进行测试对比'
        )
    
    def handle(self, *args, **options):
        url = options['url']
        timeout = options['timeout']
        disable_proxy = options['disable_proxy']
        
        # 获取代理设置
        proxies = None if disable_proxy else get_proxy_from_env() or settings.PROXY_SETTINGS
        
        self.stdout.write(self.style.WARNING(f"\n开始测试连接: {url}"))
        if proxies:
            self.stdout.write(f"使用代理: {proxies}")
        else:
            self.stdout.write(self.style.WARNING("不使用代理"))
        
        session = requests.Session()
        
        if proxies:
            session.proxies.update(proxies)
        
        # 设置UA标识，避免被拦截
        headers = {
            'User-Agent': 'GameHub/1.0 Connection Test',
        }
        
        try:
            self.stdout.write("连接中...")
            start_time = time.time()
            
            # 使用HEAD请求，避免下载大量数据
            response = session.head(url, timeout=timeout, headers=headers)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if 200 <= response.status_code < 400:
                self.stdout.write(self.style.SUCCESS(
                    f"连接成功! 状态码: {response.status_code}, 耗时: {duration:.2f}秒"
                ))
                
                # 尝试完整的GET请求
                self.stdout.write("正在进行GET请求测试...")
                start_time = time.time()
                get_response = session.get(url, timeout=timeout, headers=headers)
                end_time = time.time()
                duration = end_time - start_time
                
                self.stdout.write(self.style.SUCCESS(
                    f"GET请求成功! 状态码: {get_response.status_code}, 耗时: {duration:.2f}秒"
                ))
                
                return True
            else:
                self.stdout.write(self.style.ERROR(
                    f"连接返回错误状态码: {response.status_code}, 耗时: {duration:.2f}秒"
                ))
                return False
                
        except requests.ConnectTimeout:
            self.stdout.write(self.style.ERROR(f"连接超时 ({timeout}秒)"))
            self.stdout.write(self.style.WARNING("可能原因: 代理服务器未启动或代理配置错误"))
            return False
        except requests.ReadTimeout:
            self.stdout.write(self.style.ERROR(f"读取响应超时 ({timeout}秒)"))
            self.stdout.write(self.style.WARNING("可能原因: 代理服务器响应缓慢"))
            return False
        except requests.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f"连接错误: {e}"))
            self.stdout.write(self.style.WARNING("可能原因: 网络问题或代理服务器无法连接"))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"未知错误: {e}"))
            return False 