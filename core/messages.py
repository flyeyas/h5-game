from django.contrib.messages.storage.session import SessionStorage

class SeparatedMessagesStorage(SessionStorage):
    """
    自定义消息存储类，用于区分前台和后台消息
    """
    session_frontend_key = '_frontend_messages'
    session_admin_key = '_admin_messages'
    
    def _get(self, *args, **kwargs):
        """
        从session中获取消息，根据请求类型决定获取前台还是后台消息
        """
        # 确定当前请求是前台还是后台
        is_admin = getattr(self.request, 'is_admin', False)
        
        # 使用对应的session key
        if is_admin:
            self.session_key = self.session_admin_key
        else:
            self.session_key = self.session_frontend_key
        
        # 调用父类方法获取消息
        return super()._get(*args, **kwargs)
    
    def _store(self, messages, response, *args, **kwargs):
        """
        存储消息到session，根据请求类型决定存储到前台还是后台消息中
        """
        # 确定当前请求是前台还是后台
        is_admin = getattr(self.request, 'is_admin', False)
        
        # 使用对应的session key
        if is_admin:
            self.session_key = self.session_admin_key
        else:
            self.session_key = self.session_frontend_key
        
        # 调用父类方法存储消息
        return super()._store(messages, response, *args, **kwargs) 