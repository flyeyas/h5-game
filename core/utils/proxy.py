"""
代理工具模块
提供代理相关的辅助功能
"""

import os
import logging
import socket
import requests
import traceback
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def get_proxy_from_env():
    """
    从环境变量中获取代理设置
    
    返回:
        dict: 包含http和https代理的字典，如果环境变量未设置则返回None
    """
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    no_proxy = os.environ.get('NO_PROXY') or os.environ.get('no_proxy')
    
    if http_proxy or https_proxy:
        proxies = {}
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        
        logger.info(f"从环境变量加载代理设置: {proxies}")
        
        if no_proxy:
            logger.info(f"不使用代理的域名: {no_proxy}")
        
        return proxies
    
    return None

def setup_requests_with_proxy(session):
    """
    为requests会话设置代理
    
    参数:
        session: requests.Session对象
    
    返回:
        requests.Session: 配置了代理的Session对象
    """
    proxies = get_proxy_from_env()
    if proxies:
        session.proxies.update(proxies)
        logger.info("已为请求设置代理")
    
    return session

def is_proxy_needed(url):
    """
    判断给定URL是否需要代理访问
    可以根据需要扩展，例如根据域名列表判断
    
    参数:
        url: str, 要访问的URL
    
    返回:
        bool: 是否需要代理
    """
    # 这里可以添加逻辑来判断特定域名是否需要代理
    proxy_domains = [
        'google.com',
        'googleapis.com',
        'accounts.google.com',
        'oauth2.googleapis.com',
        'facebook.com',
        'graph.facebook.com',
        'api.twitter.com',
        'github.com',
        'api.github.com'
    ]
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    # 检查是否在需要代理的域名列表中
    needs_proxy = any(proxy_domain in domain for proxy_domain in proxy_domains)
    
    if needs_proxy:
        logger.debug(f"域名 {domain} 需要使用代理")
    
    return needs_proxy

def test_proxy_connection(proxy_url, test_url='https://www.google.com', timeout=10):
    """
    测试代理连接是否可用
    
    参数:
        proxy_url: str, 代理URL，如 http://127.0.0.1:7890
        test_url: str, 用于测试的URL
        timeout: int, 超时时间（秒）
        
    返回:
        bool: 代理是否可用
    """
    try:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        logger.info(f"正在测试代理连接: {proxy_url} -> {test_url}")
        
        response = requests.get(
            test_url, 
            proxies=proxies, 
            timeout=timeout,
            headers={'User-Agent': 'GameHub/1.0 ProxyTest'}
        )
        
        if response.status_code == 200:
            logger.info(f"代理连接测试成功: {proxy_url}")
            return True
        else:
            logger.warning(f"代理连接测试失败: 状态码 {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"代理连接测试异常: {e}")
        logger.debug(traceback.format_exc())
        return False
    except Exception as e:
        logger.error(f"代理测试过程中出现未知错误: {e}")
        logger.debug(traceback.format_exc())
        return False

def get_available_proxy():
    """
    获取可用的代理
    
    返回:
        dict: 可用的代理配置，如果没有可用代理则返回None
    """
    # 首先尝试从环境变量获取代理
    env_proxies = get_proxy_from_env()
    if env_proxies:
        http_proxy = env_proxies.get('http')
        if http_proxy and test_proxy_connection(http_proxy):
            return env_proxies
    
    # 尝试常见的本地代理端口
    common_local_proxies = [
        'http://localhost:7890',  # Clash
        'http://127.0.0.1:7890',  # Clash
        'http://localhost:1080',  # 常见SOCKS代理端口
        'http://127.0.0.1:1080',
        'http://localhost:8080',  # 常见HTTP代理端口
        'http://127.0.0.1:8080',
        'http://localhost:8118',  # Privoxy
        'http://127.0.0.1:8118'
    ]
    
    for proxy in common_local_proxies:
        if test_proxy_connection(proxy):
            logger.info(f"发现可用的本地代理: {proxy}")
            return {'http': proxy, 'https': proxy}
    
    logger.warning("未找到可用的代理")
    return None 