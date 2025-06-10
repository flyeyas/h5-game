# Google AdSense API 配置示例
# 将此配置添加到您的 html5games/settings.py 文件中

# Google AdSense API 配置
# 获取这些值的步骤：
# 1. 访问 Google Cloud Console (https://console.cloud.google.com/)
# 2. 创建新项目或选择现有项目
# 3. 启用 AdSense Management API
# 4. 创建服务账户并下载JSON密钥文件
# 5. 将JSON文件路径设置为 CREDENTIALS_FILE

GOOGLE_ADSENSE_API_CONFIG = {
    # Google服务账户JSON密钥文件路径
    # 请将此路径替换为您的实际服务账户密钥文件路径
    # 例如: '/path/to/your/service-account-key.json'
    # 或相对路径: 'credentials/adsense-service-account.json'
    'CREDENTIALS_FILE': 'path/to/your/service-account-key.json',
    
    # Google AdSense API配置
    'API_VERSION': 'v2',  # AdSense Management API 版本
    'SCOPES': [
        'https://www.googleapis.com/auth/adsense.readonly'  # 只读权限
        # 如果需要写权限，可以使用：
        # 'https://www.googleapis.com/auth/adsense'
    ],
    
    # API缓存设置（秒）
    'CACHE_TIMEOUT': 300,  # 5分钟，可根据需要调整
    
    # API请求限制
    'QUOTA_USER': 'html5games-app',  # 您的应用名称，用于配额管理
    'REQUEST_TIMEOUT': 30,  # 30秒请求超时
    
    # 日志设置
    'LOG_LEVEL': 'INFO',  # 可选: DEBUG, INFO, WARNING, ERROR
    'LOG_FILE': 'logs/adsense_api.log',  # 日志文件路径
}

# 缓存配置（用于AdSense API响应缓存）
# 如果您的 settings.py 中还没有 CACHES 配置，请添加以下内容：
"""
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5分钟默认超时
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    },
    'adsense': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'adsense-cache',
        'TIMEOUT': GOOGLE_ADSENSE_API_CONFIG['CACHE_TIMEOUT'],
        'OPTIONS': {
            'MAX_ENTRIES': 100,
            'CULL_FREQUENCY': 2,
        }
    }
}
"""

# 配置说明：
# 
# CREDENTIALS_FILE: 
#   - 这是最重要的配置项
#   - 必须指向您从 Google Cloud Console 下载的服务账户JSON密钥文件
#   - 可以使用绝对路径或相对于项目根目录的相对路径
#   - 确保文件存在且Django应用有读取权限
#
# API_VERSION:
#   - 目前推荐使用 'v2'
#   - 这是最新的AdSense Management API版本
#
# SCOPES:
#   - 'https://www.googleapis.com/auth/adsense.readonly' 提供只读权限
#   - 'https://www.googleapis.com/auth/adsense' 提供完整权限
#   - 根据您的需求选择合适的权限范围
#
# CACHE_TIMEOUT:
#   - 控制API响应的缓存时间
#   - 较长的缓存时间可以减少API调用次数，但数据可能不够实时
#   - 较短的缓存时间提供更实时的数据，但会增加API调用次数
#
# QUOTA_USER:
#   - 用于API配额管理和监控
#   - 建议设置为您的应用名称
#
# REQUEST_TIMEOUT:
#   - API请求的超时时间（秒）
#   - 如果网络较慢，可以适当增加这个值
#
# LOG_LEVEL:
#   - DEBUG: 详细的调试信息
#   - INFO: 一般信息
#   - WARNING: 警告信息
#   - ERROR: 只记录错误
#
# LOG_FILE:
#   - AdSense API相关日志的存储位置
#   - 确保目录存在且Django应用有写入权限

# 安全提醒：
# 1. 永远不要将服务账户JSON密钥文件提交到版本控制系统
# 2. 确保密钥文件的访问权限设置正确
# 3. 定期轮换服务账户密钥
# 4. 在生产环境中使用专门的生产服务账户
