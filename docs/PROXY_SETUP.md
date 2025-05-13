# 代理设置指南

在某些网络环境下，可能需要通过代理服务器才能访问Google OAuth2服务。本指南将帮助您配置和测试代理设置。

## 配置方法

### 方法一：通过环境变量配置（推荐）

设置以下环境变量：

```bash
# Linux/Mac
export HTTP_PROXY=http://your-proxy-server:port
export HTTPS_PROXY=http://your-proxy-server:port

# Windows CMD
set HTTP_PROXY=http://your-proxy-server:port
set HTTPS_PROXY=http://your-proxy-server:port

# Windows PowerShell
$env:HTTP_PROXY = "http://your-proxy-server:port"
$env:HTTPS_PROXY = "http://your-proxy-server:port"
```

### 方法二：直接修改Django配置

编辑 `gamehub/settings.py` 文件，更新代理设置：

```python
# 代理设置
PROXY_SETTINGS = {
    'http': 'http://your-proxy-server:port',
    'https': 'http://your-proxy-server:port',
}
```

## 常用代理地址

如果您使用本地代理工具，常见的代理地址有：

- HTTP代理： `http://127.0.0.1:7890`
- SOCKS5代理： `socks5://127.0.0.1:1080`

不同代理工具的默认端口可能不同，请查阅相应工具的文档。

## 测试代理连接

我们提供了一个命令行工具来测试代理连接：

```bash
# 使用代理测试连接
python manage.py test_proxy

# 设置更长的超时时间
python manage.py test_proxy --timeout 20

# 测试特定URL
python manage.py test_proxy --url https://accounts.google.com

# 不使用代理进行测试（对比）
python manage.py test_proxy --disable-proxy
```

## 排查常见问题

### 连接超时

如果看到以下错误：

```
ConnectTimeout: HTTPSConnectionPool(host='oauth2.googleapis.com', port=443): Max retries exceeded with url: /token (Caused by ConnectTimeoutError)
```

可能的原因：

1. 代理服务器未启动
2. 代理服务器地址或端口配置错误
3. 代理服务器无法连接到目标服务器

解决方法：

1. 确认代理服务器是否正常运行
2. 使用 `test_proxy` 命令测试连接
3. 尝试增加超时时间

### 代理认证失败

如果您的代理需要认证，请使用以下格式配置：

```
http://username:password@proxy-server:port
```

例如：

```python
PROXY_SETTINGS = {
    'http': 'http://user:pass@127.0.0.1:7890',
    'https': 'http://user:pass@127.0.0.1:7890',
}
```

## 安全注意事项

1. 不要在代码仓库中提交包含实际代理用户名和密码的配置文件
2. 建议使用环境变量或本地配置文件存储敏感信息
3. 在生产环境中，确保使用安全的代理服务器 