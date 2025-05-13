# 会员订阅支付实现方案

## 项目背景

H5游戏平台需要实现会员订阅功能，使用户能够通过多种支付方式开通会员服务。该功能将基于django-plans-payments框架实现，同时支持多种支付网关的配置。

## 项目结构

本项目按照Django最佳实践组织代码，主要应用包括：

- **core**: 核心数据模型和共享功能
- **admin_panel**: 管理后台应用，负责会员计划配置和支付网关管理
- **games**: 前台应用，负责展示会员计划并处理用户订阅流程

支付功能将在这三个应用之间进行适当的职责划分：
- 在**core**中定义基础数据模型
- 在**admin_panel**中实现支付网关配置和会员计划管理
- 在**games**中实现前台购买流程和用户会员中心

## 核心功能需求

- 会员订阅计划管理
- 支付网关配置
- 订阅购买流程
- 订阅状态管理

## 数据模型设计

### SubscriptionPlan模型
- 名称（如"月度会员"、"年度会员"）
- 价格
- 周期（月/年）
- 描述
- 状态（启用/禁用）

### PaymentGateway模型
- 名称（如PayPal、Stripe等）
- 状态（启用/禁用）
- 配置JSON（存储网关配置信息）

### Subscription模型
- 用户
- 订阅计划
- 开始日期
- 到期日期
- 状态（活跃/已取消/已过期）
- 支付网关
- 支付网关订阅ID

## 支持的支付网关

计划支持以下支付网关：
- PayPal
- Stripe
- 支付宝
- 微信支付
- Braintree
- Adyen

网关支持可根据实际需求选择性实现，优先实现主流网关。

## 后台管理功能

以下功能将在**admin_panel**应用中实现：

### 订阅计划管理
- 创建和编辑订阅计划
- 设置价格和周期
- 启用/禁用计划

### 支付网关配置
- 选择启用的支付网关
- 配置每个网关的必要参数（详见下文）
- 测试支付连接

#### 支付网关配置参数详情

##### PayPal 配置参数
- 环境选择（沙盒/生产）
- 商家邮箱（Business Email）
- Client ID
- Secret Key
- 货币设置（默认币种）
- 语言设置
- 返回URL（支付成功后跳转）
- 取消URL（用户取消支付后跳转）
- IPN通知URL（Instant Payment Notification回调地址）

##### Stripe 配置参数
- API密钥（Secret Key）
- 公开密钥（Publishable Key）
- Webhook密钥（Webhook Secret）
- 账户ID（Account ID，可选）
- 支持的支付方式（信用卡、Apple Pay、Google Pay等）
- 3D Secure设置（是否启用）
- 语言设置
- 默认货币
- 自动续费设置（是否启用）

##### 支付宝配置参数
- 应用ID（App ID）
- 应用私钥（App Private Key）
- 支付宝公钥（Alipay Public Key）
- 签名方式（RSA2/RSA）
- 网关地址（默认/国际版）
- 回调通知URL
- 返回URL
- 是否启用同步返回
- 默认币种（CNY）

##### 微信支付配置参数
- 商户ID（Merchant ID）
- 商户密钥（Merchant Key）
- 应用ID（App ID）
- API密钥（API Key）
- 证书路径（apiclient_cert.pem和apiclient_key.pem）
- 通知回调URL
- 支付类型（JSAPI/NATIVE/APP）
- 默认币种（CNY）

##### Braintree 配置参数
- 环境设置（沙盒/生产）
- 商家ID（Merchant ID）
- 公开密钥（Public Key）
- 私有密钥（Private Key）
- 商家账户ID（Merchant Account ID）
- 默认货币
- 计划ID（用于订阅服务）
- 是否使用3D Secure验证
- 回调通知URL

##### Adyen 配置参数
- 环境设置（测试/生产）
- 商家账户（Merchant Account）
- API密钥（API Key）
- Client Key
- HMAC密钥（用于验证通知）
- 默认货币
- 支持的支付方式
- 通知URL
- 重定向URL（成功/失败）

### 会员管理
- 查看所有会员订阅
- 手动调整订阅状态
- 查看支付历史

## 前台用户流程

以下功能将在**games**应用中实现：

### 订阅流程
1. 用户选择会员计划
2. 选择支付方式
3. 完成支付
4. 自动激活会员权限

### 会员中心
- 查看当前订阅状态
- 管理订阅（取消、更新）
- 查看支付历史

## 技术实现

### 支付处理
- 集成django-plans-payments处理订阅逻辑
- 创建支付网关适配器处理不同网关
- 实现webhook接收支付状态通知

### 会员权限
- 会员状态检查中间件
- 基于订阅状态的权限控制
- 自动提醒即将到期的会员

## 安全考虑

- 支付信息加密存储
- 支付网关配置密钥的安全处理
- HTTPS安全连接
- 支付状态验证
- 防重放攻击（使用签名和时间戳）
- 参数校验和过滤
- 日志记录和异常监控

## 部署事项

- 确保HTTPS安全连接
- 配置webhook接收URL
- 设置定时任务检查订阅状态
- 配置负载均衡（处理高并发支付请求）
- 数据库优化（支付相关表的索引和查询优化）
- 支付网关配置的备份和恢复方案

## 开发计划

1. 创建基础数据模型
2. 实现后台管理界面
3. 集成PayPal支付网关（作为首选支付方式）
4. 实现前台订阅流程
5. 添加会员权限控制
6. 集成其他支付网关
7. 测试和优化

## PayPal集成实施计划

作为首选的支付网关，PayPal集成将分为以下几个阶段：

### 第一阶段：环境搭建
1. 注册PayPal开发者账户
2. 在PayPal开发者控制台创建应用
3. 获取沙盒环境的API凭证
4. 安装必要的Python依赖包（django-paypal或paypalrestsdk）
5. 在项目设置中配置PayPal基础参数

### 第二阶段：后台配置
1. 在**admin_panel**应用中实现PayPal网关配置页面
2. 开发配置测试功能（验证API凭证有效性）
3. 添加沙盒/生产环境切换功能
4. 实现PayPal配置的加密存储
5. 创建管理员操作日志记录功能

### 第三阶段：订阅流程开发
1. 实现会员计划与PayPal产品/计划的映射
2. 在**games**应用中开发订阅创建流程
3. 设计支付流程UI界面
4. 集成PayPal的JavaScript SDK（前端集成）
5. 处理成功支付后的订阅激活
6. 在用户个人中心显示会员状态

### 第四阶段：Webhook处理
1. 配置PayPal Webhook通知
2. 在**games**应用中开发Webhook接收端点
3. 实现订阅状态变更处理
   - 支付成功
   - 支付失败
   - 订阅取消
   - 订阅更新
   - 订阅到期
4. 实现支付事件的日志记录

### 第五阶段：测试和优化
1. 使用PayPal沙盒账户进行完整流程测试
2. 模拟各种边缘情况（支付失败、网络中断等）
3. 压力测试支付处理能力
4. 优化用户体验和错误处理

### 第六阶段：上线准备
1. 切换到PayPal生产环境
2. 配置真实的商家账户
3. 进行小规模测试交易
4. 监控和记录支付流程
5. 准备运营文档和用户指南

完成PayPal集成后，可以参照类似流程集成其他支付网关，复用已有的架构和界面设计。

## 技术架构

### 代码组织
- **core/models.py**: 定义支付和订阅相关的基础数据模型
- **admin_panel/views/payment_config.py**: 实现支付网关配置界面
- **admin_panel/views/subscription_plans.py**: 实现会员计划管理
- **games/views/payment.py**: 实现前台支付流程
- **games/views/webhooks.py**: 实现支付回调处理
- **games/views/member_center.py**: 实现会员中心功能

### 模板结构
项目使用集中的**templates**目录存放所有模板文件，按应用和功能进行组织：

- **templates/admin_panel/payments/**
  - **gateway_list.html**: 支付网关列表页面
  - **gateway_form.html**: 支付网关配置表单
  - **gateway_test.html**: 支付网关测试页面
  - **plan_list.html**: 订阅计划列表页面
  - **plan_form.html**: 订阅计划编辑表单
  - **subscription_list.html**: 用户订阅管理页面

- **templates/games/payment/**
  - **plan_selection.html**: 会员计划选择页面
  - **checkout.html**: 结账页面
  - **payment_method.html**: 支付方式选择页面
  - **payment_processing.html**: 支付处理中页面
  - **payment_success.html**: 支付成功页面
  - **payment_error.html**: 支付错误页面

- **templates/games/member/**
  - **subscription.html**: 用户订阅信息页面
  - **history.html**: 支付历史记录页面
  - **manage.html**: 订阅管理页面

### 数据流程
1. 管理员在**admin_panel**中配置支付网关和会员计划
2. 用户在**games**前台选择会员计划并进行支付
3. 支付网关处理支付并通过webhook回调通知支付结果
4. **games**应用中的webhook处理器更新订阅状态
5. 用户在会员中心查看和管理订阅信息 