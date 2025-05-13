# 支付网关配置菜单设置

本文档说明如何将支付网关配置相关的菜单项添加到网站后台菜单中。

## 方法一：使用Django管理命令

我们提供了一个Django管理命令来自动添加支付网关配置相关的菜单项。执行以下命令：

```bash
python manage.py update_payment_menus
```

此命令将会添加以下菜单项：
- 支付网关管理（主菜单）
  - 网关管理
  - PayPal配置
  - 支付宝配置
  - 微信支付配置
  - Stripe配置
  - Braintree配置
  - Adyen配置
  - 会员价格
  - 交易记录

如果菜单项已存在，将会更新菜单项的URL和图标等信息。

## 方法二：使用Python脚本

如果您希望手动控制菜单项的添加，可以使用我们提供的Python脚本：

```bash
python manage.py shell < scripts/create_payment_menus.py
```

此脚本会执行与管理命令相同的操作，但允许您在执行前查看和修改脚本内容。

## 方法三：使用SQL脚本

如果您希望直接在数据库中添加菜单项，可以使用我们提供的SQL脚本：

```bash
mysql -u username -p database_name < scripts/insert_payment_menu_items.sql
```

或者通过数据库管理工具（如phpMyAdmin、DBeaver等）运行 `scripts/insert_payment_menu_items.sql` 脚本。

## 菜单项结构

添加的菜单项结构如下：

| 菜单名称 | URL | 图标 | 顺序 |
|---------|-----|------|------|
| 支付网关管理 | /admin/payment-gateway/ | fas fa-credit-card | 30 |
| 网关管理 | /admin/payment-gateway/ | fas fa-cogs | 1 |
| PayPal配置 | /admin/payment-gateway/paypal/ | fab fa-paypal | 2 |
| 支付宝配置 | /admin/payment-gateway/alipay/ | fas fa-yen-sign | 3 |
| 微信支付配置 | /admin/payment-gateway/wechatpay/ | fab fa-weixin | 4 |
| Stripe配置 | /admin/payment-gateway/stripe/ | fab fa-stripe-s | 5 |
| Braintree配置 | /admin/payment-gateway/braintree/ | fas fa-money-check-alt | 6 |
| Adyen配置 | /admin/payment-gateway/adyen/ | fas fa-money-bill-wave | 7 |
| 会员价格 | /admin/payment-gateway/membership-price/ | fas fa-tags | 8 |
| 交易记录 | /admin/payment-gateway/transactions/ | fas fa-receipt | 9 |

## 菜单图标

菜单图标使用FontAwesome图标库，更多图标可以在[FontAwesome官网](https://fontawesome.com/icons)查看。 