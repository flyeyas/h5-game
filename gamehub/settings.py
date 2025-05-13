import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-h5game-secret-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 第三方应用
    'colorfield',  # 颜色选择字段
    # django-allauth 相关应用
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # 自定义应用
    'core',  # 核心数据模型 - 放在最前面以优先加载
    'admin_panel',  # 后台管理模块
    'games',  # 前台游戏模块
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.MessageSeparationMiddleware',  # 添加消息分离中间件
    # django-allauth 中间件
    'allauth.account.middleware.AccountMiddleware',
]

# 配置消息标签，将Django的消息级别映射到Bootstrap的alert类
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',  # 将ERROR映射到Bootstrap的danger
}

# 使用自定义消息存储，区分前台和后台消息
MESSAGE_STORAGE = 'core.messages.SeparatedMessagesStorage'

ROOT_URLCONF = 'gamehub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),  # 模板目录
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'admin_panel.context_processors.admin_menu',  # 添加自定义上下文处理器，提供菜单数据
                'games.context_processors.game_categories',  # 添加游戏分类数据
                'games.context_processors.user_login_status',  # 添加用户登录状态信息
                'games.context_processors.member_content_settings',  # 添加会员内容显示配置
                'games.context_processors.auth_settings',  # 添加登录注册功能控制配置
            ],
        },
    },
]

WSGI_APPLICATION = 'gamehub.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 认证后端配置
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Django默认的认证后端
    'allauth.account.auth_backends.AuthenticationBackend',  # django-allauth的认证后端
    'core.user_auth.EmailOrUsernameModelBackend',  # 自定义认证后端，支持邮箱或用户名登录
]

# 默认用户模型设置
AUTH_USER_MODEL = 'auth.User'  # 使用Django默认的User模型

# 会话设置
SESSION_COOKIE_AGE = 1800  # 30分钟
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求都保存会话

# Internationalization
LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True

# 支持的语言
LANGUAGES = [
    ('zh-hans', '中文'),
    ('en', 'English'),
]

# 语言文件路径
LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 登录页面URL
LOGIN_URL = '/accounts/login/'

# 登录成功后的重定向URL
LOGIN_REDIRECT_URL = '/'

# 全局日志级别设置
LOG_LEVEL = 'INFO'  # 可选值: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}.{funcName}:{lineno} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_backend': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'backend.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_frontend': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'frontend.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',  # 邮件通知保持ERROR级别，不受全局设置影响
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_backend'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'file_backend'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'admin_panel': {
            'handlers': ['console', 'file_backend'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'admin': {
            'handlers': ['console', 'file_backend'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'core': {
            'handlers': ['console', 'file_backend', 'file_frontend'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'games': {
            'handlers': ['console', 'file_frontend'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
    },
}

# Django-allauth 设置
SITE_ID = 1

# 新的配置方式，替换弃用的设置
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True

# 社交账号登录成功后的重定向URL
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True

# 使用自定义模板
ACCOUNT_ADAPTER = 'games.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'games.adapters.CustomSocialAccountAdapter'

# 使用自定义表单
ACCOUNT_FORMS = {
    'signup': 'games.forms.CustomSignupForm',
}

# 模板路径设置
ACCOUNT_TEMPLATE_EXTENSION = 'html'
ACCOUNT_LOGIN_TEMPLATE = 'games/registration/login.html'
ACCOUNT_SIGNUP_TEMPLATE = 'games/registration/register.html'
ACCOUNT_LOGOUT_TEMPLATE = 'games/registration/logout.html'

# Google登录配置
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'REQUESTS_TIMEOUT': 60,  # 超时时间60秒
        'REQUESTS_PARAMS': {
            'verify': True,  # 验证SSL证书
        },
    }
}