from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    自定义认证后端，支持使用用户名或邮箱进行登录
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写authenticate方法，支持邮箱和用户名登录
        
        Args:
            request: HTTP请求对象
            username: 用户输入的用户名或邮箱
            password: 用户输入的密码
            
        Returns:
            User对象 或 None
        """
        UserModel = get_user_model()
        
        try:
            # 使用Q对象构造OR查询，支持用户名或邮箱查询
            user = UserModel.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
            
            # 如果找到用户并且密码正确，返回用户对象
            if user and user.check_password(password):
                return user
                
        except UserModel.DoesNotExist:
            # 用户不存在时，返回None
            return None
            
        # 用户不存在或密码错误时，返回None
        return None 