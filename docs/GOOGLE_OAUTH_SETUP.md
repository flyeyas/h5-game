# Google OAuth 登录配置指南

本文档提供了如何配置 Google OAuth 以实现用户通过 Google 账号登录的完整步骤。

## 步骤 1: 创建 Google API 项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 点击右上角的"创建项目"按钮
3. 输入项目名称（例如："GameHub"）
4. 点击"创建"按钮

## 步骤 2: 配置 OAuth 同意屏幕

1. 在左侧导航栏中，选择"API和服务" > "OAuth 同意屏幕"
2. 选择用户类型（建议选择"外部"，允许任何 Google 用户登录）
3. 点击"创建"按钮
4. 填写应用名称和用户支持电子邮件等必填信息
5. 在"授权域名"中添加你的网站域名（例如：`example.com`）
6. 添加开发者联系信息
7. 点击"保存并继续"
8. 在范围页面上，添加以下范围：
   - `./auth/userinfo.email`
   - `./auth/userinfo.profile`
9. 点击"保存并继续"
10. 在测试用户页面，如果处于测试阶段，添加测试用户，否则可以跳过
11. 点击"保存并继续"
12. 确认信息无误后，点击"返回仪表板"

## 步骤 3: 创建 OAuth 客户端 ID

1. 在左侧导航栏中，选择"API和服务" > "凭据"
2. 点击"创建凭据" > "OAuth 客户端 ID"
3. 选择应用类型为"Web 应用"
4. 输入名称（例如："GameHub Web Client"）
5. 在"已获授权的 JavaScript 来源"中添加你的网站域名（例如：`https://example.com`）
   - 开发环境可以添加：`http://localhost:8000`
6. 在"已获授权的重定向 URI"中添加以下 URI：
   - `https://example.com/accounts/google/login/callback/`
   - 开发环境可以添加：`http://localhost:8000/accounts/google/login/callback/`
7. 点击"创建"按钮
8. 系统将显示你的客户端 ID 和客户端密钥，记录这些信息，稍后会用到

## 步骤 4: 更新 Django 项目设置

1. 打开项目的 `settings.py` 文件
2. 确保已将以下配置更新为正确的 ID 和密钥：

```python
# django-allauth 设置
SITE_ID = 1

# 登录和注册设置
ACCOUNT_LOGIN_METHODS = {'username', 'email'}  # 支持用户名和邮箱登录
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']  # 注册必填字段
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # 邮箱验证设置：'none', 'optional', 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True  # 确保邮箱唯一

# 社交账号登录配置
SOCIALACCOUNT_LOGIN_ON_GET = True  # 直接通过GET请求处理登录，无需额外确认页面
ACCOUNT_LOGOUT_ON_GET = True  # 通过GET请求处理登出，无需确认页面

# Google登录配置
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '你的客户端ID',
            'secret': '你的客户端密钥',
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
```

## 步骤 5: 创建 Site 对象

1. 使用 Django 管理员账号登录后台
2. 进入 "Sites" 应用
3. 修改默认的 site 对象（ID 为 1）：
   - 将 Domain name 设置为你的网站域名（例如：`example.com`）
   - 将 Display name 设置为你的网站名称（例如：`GameHub`）
4. 点击"保存"按钮

## 步骤 6: 配置 Social App

1. 在 Django 管理后台中，进入 "Social Accounts" > "Social applications"
2. 点击"添加 Social application"按钮
3. 填写以下信息：
   - Provider: 选择 "Google"
   - Name: 输入 "Google"
   - Client id: 粘贴你的 Google 客户端 ID
   - Secret key: 粘贴你的 Google 客户端密钥
   - 选择你的网站（从 Available sites 移动到 Chosen sites）
4. 点击"保存"按钮

## 测试配置

配置完成后，用户应该能够在登录和注册页面看到"使用 Google 账号登录"的选项，点击该选项将会跳转到 Google 的登录页面进行身份验证，验证通过后将会自动创建一个新用户或将 Google 账号与现有用户关联。

## 故障排除

如果用户在 Google 登录过程中遇到问题，请检查：

1. 确保重定向 URI 配置正确且与请求中的 URI 完全匹配
2. 查看 Django 错误日志以获取详细信息
3. 确保你的网站域名已添加到 Google OAuth 同意屏幕的授权域名中
4. 如果在开发环境中测试，请使用 `http://localhost:8000` 而不是 `127.0.0.1:8000`（它们被视为不同的域）

## 注意事项

- 如果你的应用处于 Google OAuth 同意屏幕的测试状态，只有被添加为测试用户的 Google 账号能够登录
- 请妥善保管你的客户端密钥，不要将其提交到公共代码仓库
- 在生产环境中，建议启用 HTTPS 以保证安全性 