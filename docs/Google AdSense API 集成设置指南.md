# Google AdSense API 集成设置指南

本文档详细说明如何配置和使用真实的Google AdSense Management API来替换模拟验证逻辑。

## 前提条件

1. **Google Cloud Console 项目**
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建新项目或选择现有项目

2. **启用 AdSense Management API**
   - 在 Google Cloud Console 中，导航到 "APIs & Services" > "Library"
   - 搜索 "AdSense Management API"
   - 点击启用

3. **创建服务账户**
   - 导航到 "APIs & Services" > "Credentials"
   - 点击 "Create Credentials" > "Service Account"
   - 填写服务账户详细信息
   - 下载 JSON 密钥文件

## 环境配置

### 1. 安装依赖包

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 cachetools
```

### 2. Django 设置配置

在 `html5games/settings.py` 中配置 AdSense API 设置：

```python
# Google AdSense API 配置
GOOGLE_ADSENSE_API_CONFIG = {
    # Google服务账户JSON密钥文件路径
    # 请将此路径替换为您的实际服务账户密钥文件路径
    'CREDENTIALS_FILE': 'path/to/your/service-account-key.json',

    # Google AdSense API配置
    'API_VERSION': 'v2',
    'SCOPES': [
        'https://www.googleapis.com/auth/adsense.readonly'
    ],

    # API缓存设置（秒）
    'CACHE_TIMEOUT': 300,  # 5分钟

    # API请求限制
    'QUOTA_USER': 'html5games-app',  # 您的应用名称
    'REQUEST_TIMEOUT': 30,  # 30秒

    # 日志设置
    'LOG_LEVEL': 'INFO',
    'LOG_FILE': 'logs/adsense_api.log',
}
```

**重要配置说明：**
- `CREDENTIALS_FILE`: 将此路径替换为您下载的服务账户JSON密钥文件的实际路径
- `QUOTA_USER`: 可以设置为您的应用名称，用于API配额管理
- 其他设置可以根据需要调整

### 3. 服务账户权限配置

在 AdSense 账户中：
1. 登录到您的 AdSense 账户
2. 导航到 "Account" > "Access and authorization"
3. 添加服务账户邮箱地址
4. 授予适当的权限（至少需要查看权限）

## API 功能说明

### 1. Publisher ID 验证

系统会验证以下内容：
- Publisher ID 格式（ca-pub-XXXXXXXXXXXXXXXX）
- 账户是否存在且可访问
- 账户状态（活跃/暂停/待审核）

### 2. 账户信息获取

- 账户显示名称
- 账户状态
- 货币代码
- 时区信息
- 账户创建时间

### 3. 支付信息

- 支付准备状态
- 下次支付日期
- 当前余额
- 支付阈值

### 4. 收入数据

- 指定日期范围的收入报告
- 页面浏览量
- 点击次数
- 每日详细数据

## 错误处理

系统处理以下错误类型：

1. **认证错误** (401)
   - 服务账户凭据无效
   - 权限不足

2. **配额错误** (403)
   - API 配额超限
   - 访问被拒绝

3. **资源未找到** (404)
   - Publisher ID 不存在
   - 账户无法访问

4. **网络错误**
   - 连接超时
   - 网络不可达

## 缓存机制

- **验证结果缓存**: 5分钟（成功）/ 1分钟（失败）
- **收入数据缓存**: 1小时
- **账户信息缓存**: 5分钟

## 安全考虑

1. **凭据安全**
   - 服务账户 JSON 文件不应提交到版本控制
   - 在 settings.py 中正确配置文件路径
   - 定期轮换服务账户密钥

2. **API 限制**
   - 实施请求频率限制
   - 使用适当的缓存策略
   - 监控 API 配额使用情况

3. **日志记录**
   - 记录 API 请求和响应
   - 不记录敏感信息
   - 定期清理日志文件

## 测试和调试

### 1. 测试 Publisher ID

使用以下测试 Publisher ID 进行开发：
- `ca-pub-1234567890123456` (测试用途)

### 2. 日志查看

```bash
tail -f logs/adsense_api.log
```

### 3. 调试模式

在 Django settings 中设置：
```python
GOOGLE_ADSENSE_API_CONFIG['LOG_LEVEL'] = 'DEBUG'
```

## 生产部署

1. **配置设置**
   - 确保 settings.py 中的所有配置都已正确设置
   - 使用生产环境的服务账户

2. **监控**
   - 监控 API 调用成功率
   - 设置错误告警
   - 跟踪缓存命中率

3. **性能优化**
   - 调整缓存超时时间
   - 实施请求批处理
   - 使用 CDN 缓存静态响应

## 故障排除

### 常见问题

1. **"Authentication failed"**
   - 检查服务账户 JSON 文件路径
   - 验证服务账户权限
   - 确认 AdSense 账户中已添加服务账户

2. **"API quota exceeded"**
   - 检查 Google Cloud Console 中的配额使用情况
   - 实施更积极的缓存策略
   - 考虑申请配额增加

3. **"Publisher ID not found"**
   - 验证 Publisher ID 格式
   - 确认账户状态
   - 检查服务账户权限

### 联系支持

如果遇到持续问题，请联系：
- Google AdSense 支持
- Google Cloud 支持
- 项目开发团队

## 更新日志

- **v1.0.0**: 初始版本，基本 API 集成
- **v1.1.0**: 添加缓存机制和错误处理
- **v1.2.0**: 增强安全性和日志记录
