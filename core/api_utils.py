from django.http import JsonResponse

def api_response(success=True, message=None, data=None, errors=None, code=None, status=200, **kwargs):
    """
    创建统一格式的API响应
    
    参数:
        success (bool): 操作是否成功
        message (str): 响应消息，通常用于提示用户
        data (dict): 主要的响应数据
        errors (dict): 错误详情，通常用于表单验证错误等
        code (str): 业务状态码，如'unauthorized', 'not_found'等
        status (int): HTTP状态码
        **kwargs: 其他要包含在响应中的字段
    
    返回:
        JsonResponse: 格式化的JSON响应
    
    响应格式:
    {
        "success": true/false,          # 必选，操作是否成功
        "message": "操作成功/失败信息",   # 可选，用户友好的提示消息
        "data": { ... },               # 可选，主要的响应数据对象
        "errors": { ... },             # 可选，详细错误信息，通常用于表单验证
        "code": "error_code",          # 可选，业务状态码，用于客户端识别特定状态
        ...其他字段
    }
    
    业务状态码(code)说明:
    - "success": 成功 (默认)
    - "unauthorized": 未授权，用户未登录
    - "forbidden": 禁止访问，权限不足
    - "not_found": 资源未找到
    - "validation_error": 数据验证错误
    - "duplicate_entry": 数据重复
    - "rate_limit_exceeded": 请求频率超限
    - "internal_error": 内部服务器错误
    - "bad_request": 错误的请求参数
    - "service_unavailable": 服务不可用
    - "maintenance": 系统维护中
    """
    # 业务状态码字典：将字符串状态码映射到HTTP状态码
    status_code_mapping = {
        'success': 200,
        'unauthorized': 200,  # 不使用401，统一返回200
        'forbidden': 200,  # 不使用403，统一返回200
        'not_found': 200,  # 不使用404，统一返回200
        'validation_error': 200,  # 不使用400，统一返回200
        'duplicate_entry': 200,
        'rate_limit_exceeded': 200,  # 不使用429，统一返回200
        'internal_error': 200,  # 不使用500，统一返回200
        'bad_request': 200,  # 不使用400，统一返回200
        'service_unavailable': 200,  # 不使用503，统一返回200
        'maintenance': 200,
        'login_required': 200  # 登录相关，统一返回200
    }
    
    response = {
        'success': success
    }
    
    # 设置默认业务状态码
    if not code:
        code = 'success' if success else 'internal_error'
    
    # 添加业务状态码
    response['code'] = code
    
    # 添加消息（如果提供）
    if message:
        response['message'] = message
    
    # 添加数据（如果提供）
    if data:
        response['data'] = data
    
    # 添加错误信息（如果提供）
    if errors:
        response['errors'] = errors
    
    # 添加其他字段
    for key, value in kwargs.items():
        response[key] = value
    
    # 获取对应的HTTP状态码，默认为200
    http_status = status_code_mapping.get(code, 200) if status == 200 else status
    
    return JsonResponse(response, status=http_status) 