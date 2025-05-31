from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseRedirect


class BrowserLanguageDetectionMiddleware(MiddlewareMixin):
    """
    简化的浏览器语言检测中间件
    基于Django设置中的LANGUAGES进行语言检测
    """

    def process_request(self, request):
        # 先检查用户是否已有语言偏好（会话或cookie）
        if 'django_language' in request.COOKIES or translation.get_language() or hasattr(request, 'session') and 'django_language' in request.session:
            return None

        # 获取浏览器语言偏好
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if not accept_language:
            return None

        # 解析Accept-Language头
        browser_languages = []
        for language in accept_language.split(','):
            parts = language.strip().split(';q=')
            lang_code = parts[0].strip()
            # 有时语言代码包含国家代码（如en-US），我们只需要语言部分（en）
            lang_base = lang_code.split('-')[0].lower()
            browser_languages.append(lang_base)

        # 获取Django设置中支持的语言
        supported_languages = [code.lower() for code, name in settings.LANGUAGES]

        # 查找匹配的语言
        for browser_lang in browser_languages:
            if browser_lang in supported_languages:
                # 找到完整的语言代码
                for code, name in settings.LANGUAGES:
                    if code.lower() == browser_lang:
                        # 切换到该语言
                        translation.activate(code)

                        # 将语言选择保存到会话中
                        if hasattr(request, 'session'):
                            request.session['django_language'] = code

                        break
                break

        return None