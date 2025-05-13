from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin

class MessageSeparationMiddleware(MiddlewareMixin):
    """
    消息分离中间件，用于区分前台和后台的消息
    管理后台请求路径以/admin/开头的会被标记为后台消息
    """
    
    def process_request(self, request):
        # 初始化请求的消息分类（前台/后台）
        request.is_admin = request.path.startswith('/admin/')
        return None
        
    def process_response(self, request, response):
        # 由于Django消息框架会将所有消息存储在session中
        # 我们需要在消息添加到session之前区分它们
        # 这里我们不需要做任何事情，因为消息已经被存储到session中
        return response 