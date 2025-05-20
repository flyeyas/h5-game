import re
from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.urls import is_valid_path
from django.http import HttpResponseRedirect

from .models_menu_settings import WebsiteSetting, Language


class BrowserLanguageDetectionMiddleware(MiddlewareMixin):
    """
    检测浏览器语言并自动切换到相应的网站语言
    如果用户从未访问过网站，且网站启用了自动检测，将根据浏览器语言设置切换
    """
    
    def process_request(self, request):
        # 先检查用户是否已有语言偏好（会话或cookie）
        if 'django_language' in request.COOKIES or translation.get_language() or hasattr(request, 'session') and 'django_language' in request.session:
            return None
        
        # 检查是否启用了自动语言检测
        try:
            website_settings = WebsiteSetting.get_settings()
            if not website_settings.auto_detect_language:
                return None
        except:
            return None
        
        # 获取浏览器语言偏好
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if not accept_language:
            return None
        
        # 解析Accept-Language头，格式如："en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
        browser_languages = []
        for language in accept_language.split(','):
            parts = language.strip().split(';q=')
            lang_code = parts[0].strip()
            # 有时语言代码包含国家代码（如en-US），我们只需要语言部分（en）
            lang_base = lang_code.split('-')[0].lower()
            browser_languages.append(lang_base)
        
        # 获取支持的语言
        try:
            active_languages = Language.objects.filter(is_active=True)
            supported_languages = [lang.code.split('-')[0].lower() for lang in active_languages]
            
            # 查找匹配的语言
            for browser_lang in browser_languages:
                if browser_lang in supported_languages:
                    # 找到完整的语言代码
                    for lang in active_languages:
                        if lang.code.split('-')[0].lower() == browser_lang:
                            # 切换到该语言
                            language_code = lang.code
                            translation.activate(language_code)
                            
                            # 如果是修改URL语言前缀的请求，需要重定向
                            if settings.USE_I18N and hasattr(request, 'path_info') and settings.PREFIX_DEFAULT_LANGUAGE:
                                lang_prefix = '/%s' % language_code
                                
                                # 检查URL是否已有语言前缀
                                path = request.path_info
                                parts = path.split('/')
                                if len(parts) > 1 and parts[1] in [code for code, name in settings.LANGUAGES]:
                                    # 替换语言前缀
                                    parts[1] = language_code
                                    new_path = '/'.join(parts)
                                else:
                                    # 添加语言前缀
                                    new_path = lang_prefix + path
                                
                                if request.META.get('QUERY_STRING', ''):
                                    new_path = '%s?%s' % (new_path, request.META['QUERY_STRING'])
                                
                                return HttpResponseRedirect(new_path)
                            
                            # 将语言选择保存到会话中
                            if hasattr(request, 'session'):
                                request.session['django_language'] = language_code
                            
                            break
                    break
        except:
            # 如果出错，不进行任何操作
            pass
        
        return None 