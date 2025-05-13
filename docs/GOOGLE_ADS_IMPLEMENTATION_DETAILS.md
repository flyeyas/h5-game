# Google广告接入实施详情

本文档详细说明GameHub平台接入Google广告的技术实现细节和配置方案。

## 1. 开发环境配置

### 1.1 Google AdSense账号设置

1. 创建Google AdSense账号（https://www.google.com/adsense）
2. 完成网站验证流程
3. 获取AdSense发布商ID（类似格式：`pub-1234567890123456`）

### 1.2 项目配置变更

在`settings.py`中添加Google广告相关配置：

```python
# Google AdSense配置
GOOGLE_ADSENSE = {
    'enabled': True,  # 全局启用/禁用开关
    'publisher_id': 'pub-xxxxxxxxxxxxxxxx',  # AdSense发布商ID
    'test_mode': True,  # 测试模式（上线前设为False）
}

# 广告与会员关系配置
ADS_DISPLAY_SETTINGS = {
    'show_ads_to_anonymous': True,  # 向未登录用户展示广告
    'show_ads_to_free_users': True,  # 向免费用户展示广告
    # 会员广告显示策略 - 会员不显示任何广告
    'member_settings': {
        # 默认设置（适用于免费用户）
        'free_user': {
            'top_banner': True,
            'side_banner': True,
            'bottom_banner': True,
            'interstitial': True,
            'in_game_ads': True,
            'ads_between_games': True,
        },
        # 会员不显示任何广告
        'member': {
            'top_banner': False,
            'side_banner': False,
            'bottom_banner': False,
            'interstitial': False,
            'in_game_ads': False,
            'ads_between_games': False,
        }
    }
}
```

## 2. 技术实现细节

### 2.1 添加Google AdSense脚本

在`templates/games/base.html`的head部分添加AdSense脚本，并加入会员状态判断：

```html
{% if google_adsense.enabled and not is_member %}
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ google_adsense.publisher_id }}"
     crossorigin="anonymous"></script>
{% endif %}
```

### 2.2 创建广告模板标签

在`games/templatetags`目录下创建广告相关模板标签：

1. 创建`ad_tags.py`文件，实现不同类型广告的渲染逻辑
2. 支持根据用户会员状态动态控制广告展示

```python
# games/templatetags/ad_tags.py
from django import template
from django.conf import settings
from django.utils import timezone
from core.models import Subscription

register = template.Library()

@register.inclusion_tag('games/includes/display_ad.html', takes_context=True)
def display_ad(context, ad_type):
    """
    根据用户会员状态和广告类型决定是否显示广告
    
    参数:
    - context: 模板上下文
    - ad_type: 广告类型，如'top_banner', 'interstitial'等
    """
    request = context['request']
    
    # 获取会员状态 - 首先检查会话中是否已缓存会员状态
    is_member = request.session.get('is_member', None)
    
    # 如果会话中没有缓存会员状态，则查询数据库
    if is_member is None and request.user.is_authenticated:
        # 检查用户是否有有效订阅
        has_active_subscription = Subscription.objects.filter(
            user=request.user,
            status__in=['active', 'trial'],
            end_date__gt=timezone.now()
        ).exists()
        
        # 缓存会员状态到会话，避免频繁查询数据库
        is_member = has_active_subscription
        request.session['is_member'] = is_member
        # 设置会话过期时间，确保状态不会过期太久
        request.session.set_expiry(3600)  # 1小时
    
    # 如果是会员，不显示任何广告
    if is_member:
        return {'show_ad': False}
    
    # 非会员用户，根据广告设置决定是否显示广告
    adsense_settings = getattr(settings, 'GOOGLE_ADSENSE', {})
    ads_display_settings = getattr(settings, 'ADS_DISPLAY_SETTINGS', {})
    
    # 检查是否应该向当前用户展示广告
    if not adsense_settings.get('enabled', False):
        return {'show_ad': False}
    
    if not request.user.is_authenticated:
        # 未登录用户
        show_ad = ads_display_settings.get('show_ads_to_anonymous', True)
    else:
        # 免费用户
        show_ad = ads_display_settings.get('show_ads_to_free_users', True)
    
    if not show_ad:
        return {'show_ad': False}
    
    # 获取广告单元ID和广告尺寸
    ad_units = getattr(settings, 'AD_UNITS', {})
    ad_unit = ad_units.get(ad_type, {})
    
    return {
        'show_ad': True,
        'ad_type': ad_type,
        'ad_unit_id': ad_unit.get('id', ''),
        'ad_width': ad_unit.get('width', 'auto'),
        'ad_height': ad_unit.get('height', 'auto'),
        'publisher_id': adsense_settings.get('publisher_id', '')
    }
```

创建广告显示模板：

```html
{# templates/games/includes/display_ad.html #}
{% if show_ad %}
<div class="ad-container" data-ad-type="{{ ad_type }}">
    <ins class="adsbygoogle"
         style="display:block; width:{{ ad_width }}; height:{{ ad_height }};"
         data-ad-client="ca-{{ publisher_id }}"
         data-ad-slot="{{ ad_unit_id }}"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>
        (adsbygoogle = window.adsbygoogle || []).push({});
    </script>
    
    {# 为非会员显示升级提示 #}
    <div class="ad-upgrade-prompt">
        <a href="{% url 'games:subscription_plans' %}" class="btn btn-sm btn-outline-primary">
            升级为会员可移除广告
        </a>
    </div>
</div>
{% endif %}
```

### 2.3 广告位实现

#### 2.3.1 Banner广告

```html
{% load ad_tags %}

<!-- 顶部横幅广告 -->
{% display_ad 'top_banner' %}

<!-- 侧边栏广告 -->
{% display_ad 'side_banner' %}

<!-- 底部横幅广告 -->
{% display_ad 'bottom_banner' %}
```

#### 2.3.2 插页式广告

在游戏加载前使用JavaScript触发插页式广告，同时检查会员状态：

```javascript
function showInterstitialAd() {
  // 检查用户是否为会员
  const isMember = document.body.dataset.isMember === 'true';
  
  // 会员用户不显示广告
  if (isMember) {
    startGame();
    return;
  }
  
  // 非会员用户展示广告
  if (canShowAd('interstitial')) {
    // 显示插页式广告
    (adsbygoogle = window.adsbygoogle || []).push({
      adSlot: "interstitial_ad_slot_id",
      onAdClosed: function() {
        // 广告关闭后启动游戏
        startGame();
      }
    });
  } else {
    // 无法展示广告时直接启动游戏
    startGame();
  }
}

// 在页面模板中嵌入会员状态
document.body.dataset.isMember = "{{ is_member|yesno:'true,false' }}";
```

## 3. 会员系统集成

### 3.1 广告显示逻辑

基于用户会员状态决定广告展示策略的主要逻辑：

```python
def can_show_ad(request, ad_type):
    """
    根据用户会员状态决定是否显示指定类型的广告
    
    参数:
    - request: HTTP请求对象
    - ad_type: 广告类型，如'top_banner', 'interstitial'等
    
    返回:
    - bool: 是否显示广告
    """
    # 检查全局设置
    if not settings.GOOGLE_ADSENSE.get('enabled', False):
        return False
        
    # 首先检查用户是否是会员 - 会员用户不显示任何广告
    is_member = request.session.get('is_member', None)
    
    # 如果会话中没有缓存会员状态，则查询数据库
    if is_member is None and request.user.is_authenticated:
        is_member = Subscription.objects.filter(
            user=request.user,
            status__in=['active', 'trial'],
            end_date__gt=timezone.now()
        ).exists()
        
        # 缓存会员状态到会话
        request.session['is_member'] = is_member
        request.session.set_expiry(3600)  # 1小时
    
    # 如果是会员，直接返回False（不显示广告）
    if is_member:
        return False
    
    # 检查用户登录状态
    if not request.user.is_authenticated:
        return settings.ADS_DISPLAY_SETTINGS.get('show_ads_to_anonymous', True)
    
    # 未订阅的注册用户
    return settings.ADS_DISPLAY_SETTINGS.get('show_ads_to_free_users', True)
```

### 3.2 上下文处理器

创建上下文处理器，向所有模板提供广告相关变量，包括会员状态：

```python
def ads_settings(request):
    """
    提供广告显示设置的上下文处理器
    """
    adsense_settings = getattr(settings, 'GOOGLE_ADSENSE', {})
    
    # 获取用户会员状态
    is_member = request.session.get('is_member', None)
    
    # 如果会话中没有缓存会员状态，则查询数据库
    if is_member is None and request.user.is_authenticated:
        is_member = Subscription.objects.filter(
            user=request.user,
            status__in=['active', 'trial'],
            end_date__gt=timezone.now()
        ).exists()
        
        # 缓存会员状态到会话
        request.session['is_member'] = is_member
        request.session.set_expiry(3600)  # 1小时
    else:
        # 未登录用户
        is_member = False
    
    context = {
        'google_adsense': {
            'enabled': adsense_settings.get('enabled', False),
            'publisher_id': adsense_settings.get('publisher_id', ''),
            'test_mode': adsense_settings.get('test_mode', True),
        },
        'is_member': is_member  # 添加会员状态到上下文
    }
    
    # 如果是会员，所有广告位都设为不显示
    if is_member:
        context['show_ads'] = {
            'top_banner': False,
            'side_banner': False,
            'bottom_banner': False,
            'interstitial': False,
            'in_game_ads': False,
            'ads_between_games': False
        }
    else:
        # 添加各广告位的显示状态
        ad_types = ['top_banner', 'side_banner', 'bottom_banner', 
                    'interstitial', 'in_game_ads', 'ads_between_games']
        
        context['show_ads'] = {}
        for ad_type in ad_types:
            context['show_ads'][ad_type] = can_show_ad(request, ad_type)
    
    return context
```

## 4. 广告性能优化

### 4.1 会员状态检测优化

为提高性能，避免频繁查询数据库检查会员状态：

```javascript
// 在用户订阅状态变更时更新会话
document.addEventListener('DOMContentLoaded', function() {
    // 监听订阅成功事件
    const subscriptionForm = document.getElementById('subscription-form');
    if (subscriptionForm) {
        subscriptionForm.addEventListener('subscription-success', function() {
            // 更新本地会员状态
            document.body.dataset.isMember = 'true';
            
            // 向服务器发送请求更新会话
            fetch('/api/update-member-status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    is_member: true
                })
            });
            
            // 刷新页面移除广告
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        });
    }
});

// 获取CSRF令牌
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}
```

### 4.2 延迟加载广告

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否为会员
    const isMember = document.body.dataset.isMember === 'true';
    
    // 会员用户不加载广告
    if (isMember) {
        return;
    }
    
    // 非会员用户延迟加载广告
    setTimeout(function() {
        loadAdContents();
    }, 1000);
});

function loadAdContents() {
    // 查找页面中的广告容器并按需加载
    const adContainers = document.querySelectorAll('.ad-container[data-ad-load="lazy"]');
    
    adContainers.forEach(container => {
        // 检查广告容器是否在可视区域内
        if (isElementInViewport(container)) {
            const adType = container.getAttribute('data-ad-type');
            const adCode = getAdCode(adType);
            container.innerHTML = adCode;
            container.setAttribute('data-ad-loaded', 'true');
            
            // 初始化广告
            (adsbygoogle = window.adsbygoogle || []).push({});
        }
    });
}
```

## 5. 隐私和合规性实现

### 5.1 Cookie同意机制

为符合隐私法规，实现Cookie同意机制，同时考虑会员状态：

```html
<div id="cookie-consent" class="cookie-banner">
    <div class="container">
        <p>
            本网站使用Cookie和类似技术来改善您的体验，包括个性化内容和广告。
            继续使用本网站即表示您同意我们使用这些技术。
            了解更多信息，请查看我们的<a href="/privacy-policy">隐私政策</a>。
        </p>
        <div class="cookie-buttons">
            <button id="accept-cookies" class="btn btn-primary">接受</button>
            <button id="reject-cookies" class="btn btn-outline-secondary">仅接受必要Cookie</button>
        </div>
        
        {% if not is_member %}
        <div class="mt-2">
            <a href="{% url 'games:subscription_plans' %}" class="btn btn-sm btn-outline-info">
                成为会员可获得无广告体验
            </a>
        </div>
        {% endif %}
    </div>
</div>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        const cookieConsent = document.getElementById('cookie-consent');
        const acceptBtn = document.getElementById('accept-cookies');
        const rejectBtn = document.getElementById('reject-cookies');
        
        // 检查用户是否已经设置了Cookie偏好
        if (!localStorage.getItem('cookie_preference')) {
            cookieConsent.style.display = 'block';
        }
        
        acceptBtn.addEventListener('click', function() {
            localStorage.setItem('cookie_preference', 'accept_all');
            cookieConsent.style.display = 'none';
            // 初始化广告和分析
            const isMember = document.body.dataset.isMember === 'true';
            if (!isMember) {
                initializeAdsAndAnalytics();
            }
        });
        
        rejectBtn.addEventListener('click', function() {
            localStorage.setItem('cookie_preference', 'essential_only');
            cookieConsent.style.display = 'none';
            // 仅初始化必要功能
            initializeEssentialOnly();
        });
    });
</script>
```

## 6. 监控与分析

### 6.1 广告效果跟踪

添加会员转化率跟踪：

```python
class AdImpression(models.Model):
    """广告展示记录模型"""
    user = models.ForeignKey('auth.User', verbose_name=_("用户"), on_delete=models.SET_NULL, 
                          null=True, blank=True, related_name="ad_impressions")
    ad_type = models.CharField(_("广告类型"), max_length=50)
    ad_unit_id = models.CharField(_("广告单元ID"), max_length=100)
    page_url = models.CharField(_("页面URL"), max_length=255)
    referrer = models.CharField(_("来源页面"), max_length=255, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    ip_address = models.GenericIPAddressField(_("IP地址"), blank=True, null=True)
    is_member = models.BooleanField(_("是否会员"), default=False)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    
    # 新增字段 - 追踪会员转化
    led_to_subscription = models.BooleanField(_("是否导致订阅"), default=False)
    days_to_subscription = models.IntegerField(_("广告展示到订阅的天数"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("广告展示")
        verbose_name_plural = _("广告展示")
        indexes = [
            models.Index(fields=['ad_type'], name='ad_type_idx'),
            models.Index(fields=['created_at'], name='ad_impression_date_idx'),
            models.Index(fields=['led_to_subscription'], name='led_to_subscription_idx'),
        ]
```

### 6.2 会员增长与广告关系分析

构建会员增长与广告收益关系分析仪表板：

1. 广告展示与会员转化率关系
2. 不同广告位置对会员转化的影响
3. 会员订阅增长对广告收入的影响分析
4. 会员留存率与无广告体验的关联 

## 7. iframe游戏广告实现详情

### 7.1 游戏加载前广告（iframe实施方案）

针对第三方HTML5游戏通过iframe嵌入的场景，需要在加载iframe前显示广告：

#### 7.1.1 HTML结构

```html
<!-- 游戏详情页面 -->
<div class="game-container">
    <!-- 游戏加载前广告容器 -->
    {% if not is_member %}
    <div id="pre-game-ad-container" class="interstitial-ad-container" style="display:none;">
        <div class="ad-wrapper">
            <div class="ad-content">
                {% display_ad 'pre_game_interstitial' %}
            </div>
            <div class="ad-controls">
                <div id="ad-timer">广告将在 <span id="ad-countdown">5</span> 秒后结束</div>
                <button id="skip-ad-button" style="display:none;">跳过广告</button>
            </div>
        </div>
    </div>
    {% endif %}
    
    <!-- 游戏按钮和iframe容器 -->
    <button id="start-game-button" class="btn btn-primary btn-lg">开始游戏</button>
    <div class="game-frame-container" style="display:none;">
        <iframe id="game-frame" data-game-url="{{ game.url }}" frameborder="0" scrolling="no" width="100%" height="600"></iframe>
    </div>
</div>
```

#### 7.1.2 JavaScript实现

```javascript
// 游戏加载前广告逻辑
document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('start-game-button');
    const gameFrame = document.getElementById('game-frame');
    const gameContainer = document.querySelector('.game-frame-container');
    const adContainer = document.getElementById('pre-game-ad-container');
    const skipButton = document.getElementById('skip-ad-button');
    const countdownElement = document.getElementById('ad-countdown');
    
    // 获取会员状态
    const isMember = document.body.dataset.isMember === 'true';
    
    // 游戏加载函数
    function loadGame() {
        // 获取游戏URL
        const gameUrl = gameFrame.getAttribute('data-game-url');
        
        // 设置iframe的src属性以加载游戏
        gameFrame.src = gameUrl;
        
        // 显示游戏容器
        gameContainer.style.display = 'block';
        
        // 隐藏开始按钮
        startButton.style.display = 'none';
    }
    
    // 广告倒计时函数
    function startAdCountdown() {
        let seconds = 5;
        countdownElement.textContent = seconds;
        
        const countdownInterval = setInterval(function() {
            seconds--;
            countdownElement.textContent = seconds;
            
            if (seconds <= 0) {
                clearInterval(countdownInterval);
                skipButton.style.display = 'block';
            }
        }, 1000);
        
        return countdownInterval;
    }
    
    // 记录广告展示
    function logAdImpression(adType) {
        fetch('/api/log-ad-impression/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                ad_type: adType,
                page_url: window.location.href
            })
        });
    }
    
    // 检查广告展示频率
    function checkAdFrequency(adType) {
        // 获取上次展示时间
        const lastShownTime = localStorage.getItem(`last_${adType}_ad_time`);
        const now = new Date().getTime();
        
        // 游戏加载前广告频率控制 - 10分钟内不重复展示
        if (lastShownTime && now - parseInt(lastShownTime) < 10 * 60 * 1000) {
            return false;
        }
        
        // 更新展示时间
        localStorage.setItem(`last_${adType}_ad_time`, now.toString());
        return true;
    }
    
    // 开始游戏按钮点击事件
    startButton.addEventListener('click', function() {
        if (isMember) {
            // 会员用户直接加载游戏
            loadGame();
        } else {
            // 检查是否应该显示广告（频率控制）
            if (checkAdFrequency('pre_game')) {
                // 显示广告容器
                adContainer.style.display = 'flex';
                
                // 开始倒计时
                const countdownInterval = startAdCountdown();
                
                // 记录广告展示
                logAdImpression('pre_game_interstitial');
                
                // 加载广告
                (adsbygoogle = window.adsbygoogle || []).push({
                    adSlot: 'pre_game_interstitial_1',
                    onAdLoaded: function() {
                        console.log('广告加载成功');
                    },
                    onAdFailedToLoad: function() {
                        // 广告加载失败，直接跳过
                        clearInterval(countdownInterval);
                        adContainer.style.display = 'none';
                        loadGame();
                    }
                });
                
                // 跳过广告按钮点击事件
                skipButton.addEventListener('click', function() {
                    clearInterval(countdownInterval);
                    adContainer.style.display = 'none';
                    loadGame();
                });
                
                // 设置超时保护（如果广告加载失败或其他问题）
                setTimeout(function() {
                    if (gameFrame.src === '') {
                        clearInterval(countdownInterval);
                        adContainer.style.display = 'none';
                        loadGame();
                    }
                }, 12000); // 12秒后超时
            } else {
                // 不满足广告频率条件，直接加载游戏
                loadGame();
            }
        }
    });
});
```

#### 7.1.3 CSS样式

```css
/* 插页式广告容器样式 */
.interstitial-ad-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.8);
    z-index: 9999;
    display: none;
    align-items: center;
    justify-content: center;
}

.ad-wrapper {
    background-color: #fff;
    border-radius: 8px;
    padding: 20px;
    max-width: 90%;
    max-height: 90%;
    overflow: auto;
    text-align: center;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

.ad-content {
    margin-bottom: 15px;
    min-height: 250px;
    min-width: 300px;
}

.ad-controls {
    display: flex;
    flex-direction: column;
    align-items: center;
}

#ad-timer {
    margin-bottom: 10px;
    font-size: 14px;
    color: #666;
}

#skip-ad-button {
    padding: 8px 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    display: none;
    transition: background-color 0.3s;
}

#skip-ad-button:hover {
    background-color: #45a049;
}

/* 游戏容器样式 */
.game-container {
    margin: 20px 0;
    text-align: center;
}

#start-game-button {
    margin-bottom: 20px;
    padding: 12px 30px;
    font-size: 18px;
}

.game-frame-container {
    position: relative;
    width: 100%;
    overflow: hidden;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: #f5f5f5;
}
```

### 7.2 页面切换广告

实现从游戏列表页导航到游戏详情页时显示的插页式广告：

#### 7.2.1 后端实现

在`views.py`中添加页面切换广告逻辑：

```python
from django.views.generic import DetailView
from games.models import Game
from django.core.cache import cache

class GameDetailView(DetailView):
    model = Game
    template_name = 'games/game_detail.html'
    context_object_name = 'game'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 添加页面切换广告相关上下文
        # 1. 检查用户是否是会员
        is_member = self.request.session.get('is_member', False)
        
        # 2. 检查是否应该展示页面切换广告
        show_transition_ad = False
        
        if not is_member:
            # 获取用户ID或会话ID
            user_id = self.request.user.id if self.request.user.is_authenticated else None
            session_key = self.request.session.session_key
            
            # 生成缓存键
            cache_key = f"transition_ad_{user_id or session_key}"
            
            # 检查缓存中是否有最近的广告展示记录
            last_shown = cache.get(cache_key)
            
            if not last_shown:
                # 如果没有记录，应该展示广告
                show_transition_ad = True
                
                # 设置缓存，15分钟内不再展示
                cache.set(cache_key, True, 60 * 15)  # 15分钟
        
        context['show_transition_ad'] = show_transition_ad
        return context
```

#### 7.2.2 前端实现

在游戏详情页`game_detail.html`添加页面切换广告：

```html
{% extends 'games/base.html' %}
{% load ad_tags %}

{% block content %}
<!-- 页面切换广告 -->
{% if show_transition_ad and not is_member %}
<div id="transition-ad-container" class="interstitial-ad-container">
    <div class="ad-wrapper">
        <div class="ad-content">
            {% display_ad 'transition_interstitial' %}
        </div>
        <div class="ad-controls">
            <div id="transition-ad-timer">广告将在 <span id="transition-ad-countdown">5</span> 秒后关闭</div>
            <button id="transition-skip-button" style="display:none;">跳过广告</button>
        </div>
    </div>
</div>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        const adContainer = document.getElementById('transition-ad-container');
        const skipButton = document.getElementById('transition-skip-button');
        const countdownElement = document.getElementById('transition-ad-countdown');
        
        // 显示广告容器
        adContainer.style.display = 'flex';
        
        // 开始倒计时
        let seconds = 5;
        countdownElement.textContent = seconds;
        
        const countdownInterval = setInterval(function() {
            seconds--;
            countdownElement.textContent = seconds;
            
            if (seconds <= 0) {
                clearInterval(countdownInterval);
                skipButton.style.display = 'block';
            }
        }, 1000);
        
        // 跳过按钮点击事件
        skipButton.addEventListener('click', function() {
            adContainer.style.display = 'none';
        });
        
        // 5秒后自动关闭
        setTimeout(function() {
            adContainer.style.display = 'none';
        }, 10000);
        
        // 记录广告展示
        fetch('/api/log-ad-impression/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                ad_type: 'transition_interstitial',
                page_url: window.location.href
            })
        });
    });
</script>
{% endif %}

<!-- 游戏详情内容 -->
<div class="container game-detail-container">
    <!-- 游戏内容 -->
</div>
{% endblock %}
```

### 7.3 会话开始广告

实现用户每次会话首次浏览游戏时显示的广告：

#### 7.3.1 JavaScript实现

在`base.html`中添加会话开始广告逻辑：

```html
{% if not is_member %}
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // 检查是否是新会话
        const isNewSession = checkNewSession();
        
        // 检查24小时内的广告展示次数
        const dailyAdCount = getDailyAdCount();
        
        // 如果是新会话且未超过24小时内的最大展示次数（2次）
        if (isNewSession && dailyAdCount < 2) {
            // 显示会话开始广告
            showSessionStartAd();
            
            // 更新24小时内的广告展示次数
            incrementDailyAdCount();
        }
    });
    
    // 检查是否是新会话
    function checkNewSession() {
        const sessionStarted = sessionStorage.getItem('session_start_ad_shown');
        
        if (!sessionStarted) {
            // 标记会话已开始
            sessionStorage.setItem('session_start_ad_shown', 'true');
            return true;
        }
        
        return false;
    }
    
    // 获取24小时内广告展示次数
    function getDailyAdCount() {
        const today = new Date().toISOString().split('T')[0]; // 当前日期，格式：YYYY-MM-DD
        const storedDate = localStorage.getItem('session_ad_date');
        const storedCount = localStorage.getItem('session_ad_count');
        
        // 如果没有存储记录或日期不是今天，重置计数
        if (!storedDate || storedDate !== today) {
            localStorage.setItem('session_ad_date', today);
            localStorage.setItem('session_ad_count', '0');
            return 0;
        }
        
        return parseInt(storedCount || '0');
    }
    
    // 增加24小时内广告展示次数
    function incrementDailyAdCount() {
        const today = new Date().toISOString().split('T')[0];
        const currentCount = getDailyAdCount();
        
        localStorage.setItem('session_ad_date', today);
        localStorage.setItem('session_ad_count', (currentCount + 1).toString());
    }
    
    // 显示会话开始广告
    function showSessionStartAd() {
        // 创建广告容器
        const adContainer = document.createElement('div');
        adContainer.id = 'session-start-ad';
        adContainer.className = 'interstitial-ad-container';
        adContainer.style.display = 'flex';
        
        // 广告内容HTML
        adContainer.innerHTML = `
            <div class="ad-wrapper">
                <div class="ad-content">
                    <ins class="adsbygoogle"
                         style="display:block; min-width:300px; min-height:250px"
                         data-ad-client="ca-pub-{{ google_adsense.publisher_id }}"
                         data-ad-slot="session_start_ad_slot"
                         data-ad-format="rectangle"></ins>
                </div>
                <div class="ad-controls">
                    <div class="ad-message">欢迎回到GameHub! 玩游戏之前，请看看这个广告</div>
                    <div id="session-ad-timer">广告将在 <span id="session-ad-countdown">5</span> 秒后关闭</div>
                    <button id="session-skip-button" style="display:none;">跳过广告</button>
                </div>
                <div class="membership-promo">
                    <p>升级为会员，享受无广告体验！</p>
                    <a href="/subscription/plans/" class="btn btn-sm btn-outline-primary">查看会员方案</a>
                </div>
            </div>
        `;
        
        // 添加到页面
        document.body.appendChild(adContainer);
        
        // 初始化广告
        (adsbygoogle = window.adsbygoogle || []).push({});
        
        // 开始倒计时
        let seconds = 5;
        const countdownElement = document.getElementById('session-ad-countdown');
        
        const countdownInterval = setInterval(function() {
            seconds--;
            countdownElement.textContent = seconds;
            
            if (seconds <= 0) {
                clearInterval(countdownInterval);
                document.getElementById('session-skip-button').style.display = 'block';
            }
        }, 1000);
        
        // 跳过按钮点击事件
        document.getElementById('session-skip-button').addEventListener('click', function() {
            adContainer.style.display = 'none';
            
            // 一段时间后移除DOM元素
            setTimeout(function() {
                adContainer.remove();
            }, 500);
        });
        
        // 10秒后自动关闭
        setTimeout(function() {
            adContainer.style.display = 'none';
            
            // 一段时间后移除DOM元素
            setTimeout(function() {
                adContainer.remove();
            }, 500);
        }, 10000);
        
        // 记录广告展示
        fetch('/api/log-ad-impression/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                ad_type: 'session_start_ad',
                page_url: window.location.href
            })
        });
    }
</script>
{% endif %}
```

### 7.4 后端API接口

创建用于记录广告展示和检查广告频率的API：

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json
from .models import AdImpression

@csrf_protect
@require_POST
def log_ad_impression(request):
    """记录广告展示"""
    try:
        data = json.loads(request.body)
        ad_type = data.get('ad_type')
        page_url = data.get('page_url')
        
        # 创建广告展示记录
        AdImpression.objects.create(
            user=request.user if request.user.is_authenticated else None,
            ad_type=ad_type,
            page_url=page_url,
            referrer=request.META.get('HTTP_REFERER', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=get_client_ip(request),
            is_member=request.session.get('is_member', False)
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```

### 7.5 广告频率控制

在`settings.py`中添加广告频率控制配置：

```python
# 广告频率控制设置
AD_FREQUENCY_SETTINGS = {
    'pre_game_ad': {
        'cooldown_minutes': 10,  # 同一用户10分钟内不重复展示
    },
    'transition_ad': {
        'cooldown_minutes': 15,  # 同一用户15分钟内不重复展示
    },
    'session_start_ad': {
        'max_daily': 2,  # 每24小时最多展示2次
    }
} 
```

## 8. 后台管理系统中的广告配置

为了避免直接修改配置文件，我们可以利用已有的后台配置系统来管理Google广告设置。这样可以让非技术管理人员也能方便地配置和调整广告参数。

### 8.1 配置项设计

在后台系统配置管理中添加以下Google广告配置项：

```python
# Google AdSense配置项
'google_adsense_enabled': 'true',  # 全局启用/禁用开关
'google_adsense_publisher_id': 'pub-xxxxxxxxxxxxxxxx',  # AdSense发布商ID
'google_adsense_test_mode': 'true',  # 测试模式

# 广告单元配置
'ad_units': {
    'pre_game_interstitial': {
        'id': 'pre_game_ad_slot_1',
        'width': '300',
        'height': '250'
    },
    'transition_interstitial': {
        'id': 'transition_ad_slot_1',
        'width': '300',
        'height': '250'
    },
    'session_start_ad': {
        'id': 'session_start_ad_slot_1',
        'width': '300',
        'height': '250'
    }
}

# 广告频率配置
'ad_frequency_settings': {
    'pre_game_ad': {
        'cooldown_minutes': 10
    },
    'transition_ad': {
        'cooldown_minutes': 15
    },
    'session_start_ad': {
        'max_daily': 2
    }
}

# 会员广告显示策略
'ads_display_settings': {
    'show_ads_to_anonymous': 'true',
    'show_ads_to_free_users': 'true'
}
```

### 8.2 后台界面实现

在管理后台添加Google广告配置专用页面：

1. 创建新的视图文件 `admin_panel/google_ads_settings_views.py`：

```python
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import permission_required
import json

from .models import ConfigSettings, AdminLog
from .admin_site import custom_staff_member_required

@custom_staff_member_required
@permission_required('admin_panel.setting_view', raise_exception=True)
def google_ads_settings_view(request):
    """Google广告配置管理页面"""
    # 获取或创建默认配置
    adsense_enabled = ConfigSettings.get_config('google_adsense_enabled', 'false')
    publisher_id = ConfigSettings.get_config('google_adsense_publisher_id', '')
    test_mode = ConfigSettings.get_config('google_adsense_test_mode', 'true')
    
    # 广告单元配置
    ad_units_json = ConfigSettings.get_config('ad_units', '{}')
    ad_units = json.loads(ad_units_json) if isinstance(ad_units_json, str) else ad_units_json
    
    # 广告频率设置
    ad_frequency_json = ConfigSettings.get_config('ad_frequency_settings', '{}')
    ad_frequency = json.loads(ad_frequency_json) if isinstance(ad_frequency_json, str) else ad_frequency_json
    
    # 会员广告显示策略
    ads_display_json = ConfigSettings.get_config('ads_display_settings', '{}')
    ads_display = json.loads(ads_display_json) if isinstance(ads_display_json, str) else ads_display_json
    
    # 处理表单提交
    if request.method == 'POST' and request.user.has_perm('admin_panel.setting_edit'):
        # 基本设置
        new_adsense_enabled = request.POST.get('google_adsense_enabled') == 'on'
        new_publisher_id = request.POST.get('google_adsense_publisher_id', '')
        new_test_mode = request.POST.get('google_adsense_test_mode') == 'on'
        
        # 更新基本设置
        update_config('google_adsense_enabled', str(new_adsense_enabled).lower())
        update_config('google_adsense_publisher_id', new_publisher_id)
        update_config('google_adsense_test_mode', str(new_test_mode).lower())
        
        # 更新广告单元设置
        new_ad_units = {
            'pre_game_interstitial': {
                'id': request.POST.get('pre_game_ad_id', ''),
                'width': request.POST.get('pre_game_ad_width', '300'),
                'height': request.POST.get('pre_game_ad_height', '250')
            },
            'transition_interstitial': {
                'id': request.POST.get('transition_ad_id', ''),
                'width': request.POST.get('transition_ad_width', '300'),
                'height': request.POST.get('transition_ad_height', '250')
            },
            'session_start_ad': {
                'id': request.POST.get('session_start_ad_id', ''),
                'width': request.POST.get('session_start_ad_width', '300'),
                'height': request.POST.get('session_start_ad_height', '250')
            }
        }
        update_config('ad_units', json.dumps(new_ad_units))
        
        # 更新广告频率设置
        new_ad_frequency = {
            'pre_game_ad': {
                'cooldown_minutes': int(request.POST.get('pre_game_cooldown', 10))
            },
            'transition_ad': {
                'cooldown_minutes': int(request.POST.get('transition_cooldown', 15))
            },
            'session_start_ad': {
                'max_daily': int(request.POST.get('session_max_daily', 2))
            }
        }
        update_config('ad_frequency_settings', json.dumps(new_ad_frequency))
        
        # 更新会员广告显示策略
        new_ads_display = {
            'show_ads_to_anonymous': request.POST.get('show_ads_to_anonymous') == 'on',
            'show_ads_to_free_users': request.POST.get('show_ads_to_free_users') == 'on'
        }
        update_config('ads_display_settings', json.dumps(new_ads_display))
        
        # 记录操作日志
        AdminLog.objects.create(
            admin=request.user,
            action=_("更新了Google广告配置"),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, _('Google广告配置已成功保存'))
        return redirect('admin_panel:google_ads_settings')
    
    context = {
        'title': _('Google广告配置'),
        'adsense_enabled': adsense_enabled == 'true',
        'publisher_id': publisher_id,
        'test_mode': test_mode == 'true',
        'ad_units': ad_units,
        'ad_frequency': ad_frequency,
        'ads_display': ads_display
    }
    
    return render(request, 'admin/google_ads_settings.html', context)

def update_config(key, value):
    """更新或创建配置项"""
    config, created = ConfigSettings.objects.get_or_create(
        key=key,
        defaults={
            'value': value,
            'description': f'Google广告配置: {key}',
            'is_active': True
        }
    )
    
    if not created:
        config.value = value
        config.save()
```

2. 在`admin_panel/urls.py`中添加URL路由：

```python
path('google-ads-settings/', google_ads_settings_views.google_ads_settings_view, name='google_ads_settings'),
```

3. 创建`templates/admin/google_ads_settings.html`模板：

```html
{% extends "admin/base_site.html" %}
{% load i18n %}
{% load static %}

{% block title %}{{ title }} | {{ site_title|default:_('GameHub管理系统') }}{% endblock %}

{% block content %}
<div class="container-fluid p-4">
    <h1 class="h3 mb-2 text-gray-800">{{ title }}</h1>
    <p class="mb-4">管理Google广告的配置和展示策略</p>

    <div class="row">
        <div class="col-12">
            <div class="card shadow mb-4">
                <div class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                    <h6 class="m-0 font-weight-bold text-primary">Google广告设置</h6>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        <!-- 基本设置 -->
                        <h5 class="section-title">基本设置</h5>
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="google_adsense_enabled" 
                                           name="google_adsense_enabled" {% if adsense_enabled %}checked{% endif %}>
                                    <label class="form-check-label" for="google_adsense_enabled">启用Google广告</label>
                                </div>
                                <div class="form-text">全局控制是否显示广告</div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="google_adsense_publisher_id" class="form-label">发布商ID</label>
                                    <input type="text" class="form-control" id="google_adsense_publisher_id" 
                                           name="google_adsense_publisher_id" value="{{ publisher_id }}">
                                    <div class="form-text">如：pub-1234567890123456</div>
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="google_adsense_test_mode" 
                                           name="google_adsense_test_mode" {% if test_mode %}checked{% endif %}>
                                    <label class="form-check-label" for="google_adsense_test_mode">测试模式</label>
                                </div>
                                <div class="form-text">上线前设置为关闭</div>
                            </div>
                        </div>
                        
                        <!-- 广告单元配置 -->
                        <h5 class="section-title">广告单元配置</h5>
                        <div class="row mb-4">
                            <!-- 游戏前广告 -->
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-header">
                                        <h6 class="mb-0">游戏前广告</h6>
                                    </div>
                                    <div class="card-body">
                                        <div class="mb-2">
                                            <label for="pre_game_ad_id" class="form-label">广告单元ID</label>
                                            <input type="text" class="form-control" id="pre_game_ad_id" 
                                                   name="pre_game_ad_id" value="{{ ad_units.pre_game_interstitial.id }}">
                                        </div>
                                        <div class="row">
                                            <div class="col-6">
                                                <label for="pre_game_ad_width" class="form-label">宽度</label>
                                                <input type="text" class="form-control" id="pre_game_ad_width" 
                                                       name="pre_game_ad_width" value="{{ ad_units.pre_game_interstitial.width|default:'300' }}">
                                            </div>
                                            <div class="col-6">
                                                <label for="pre_game_ad_height" class="form-label">高度</label>
                                                <input type="text" class="form-control" id="pre_game_ad_height" 
                                                       name="pre_game_ad_height" value="{{ ad_units.pre_game_interstitial.height|default:'250' }}">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 页面切换广告 -->
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-header">
                                        <h6 class="mb-0">页面切换广告</h6>
                                    </div>
                                    <div class="card-body">
                                        <div class="mb-2">
                                            <label for="transition_ad_id" class="form-label">广告单元ID</label>
                                            <input type="text" class="form-control" id="transition_ad_id" 
                                                   name="transition_ad_id" value="{{ ad_units.transition_interstitial.id }}">
                                        </div>
                                        <div class="row">
                                            <div class="col-6">
                                                <label for="transition_ad_width" class="form-label">宽度</label>
                                                <input type="text" class="form-control" id="transition_ad_width" 
                                                       name="transition_ad_width" value="{{ ad_units.transition_interstitial.width|default:'300' }}">
                                            </div>
                                            <div class="col-6">
                                                <label for="transition_ad_height" class="form-label">高度</label>
                                                <input type="text" class="form-control" id="transition_ad_height" 
                                                       name="transition_ad_height" value="{{ ad_units.transition_interstitial.height|default:'250' }}">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 会话开始广告 -->
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-header">
                                        <h6 class="mb-0">会话开始广告</h6>
                                    </div>
                                    <div class="card-body">
                                        <div class="mb-2">
                                            <label for="session_start_ad_id" class="form-label">广告单元ID</label>
                                            <input type="text" class="form-control" id="session_start_ad_id" 
                                                   name="session_start_ad_id" value="{{ ad_units.session_start_ad.id }}">
                                        </div>
                                        <div class="row">
                                            <div class="col-6">
                                                <label for="session_start_ad_width" class="form-label">宽度</label>
                                                <input type="text" class="form-control" id="session_start_ad_width" 
                                                       name="session_start_ad_width" value="{{ ad_units.session_start_ad.width|default:'300' }}">
                                            </div>
                                            <div class="col-6">
                                                <label for="session_start_ad_height" class="form-label">高度</label>
                                                <input type="text" class="form-control" id="session_start_ad_height" 
                                                       name="session_start_ad_height" value="{{ ad_units.session_start_ad.height|default:'250' }}">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 广告频率设置 -->
                        <h5 class="section-title">广告频率控制</h5>
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="pre_game_cooldown" class="form-label">游戏前广告冷却时间(分钟)</label>
                                    <input type="number" class="form-control" id="pre_game_cooldown" 
                                           name="pre_game_cooldown" value="{{ ad_frequency.pre_game_ad.cooldown_minutes|default:10 }}">
                                    <div class="form-text">同一用户在指定时间内不再展示</div>
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="transition_cooldown" class="form-label">页面切换广告冷却时间(分钟)</label>
                                    <input type="number" class="form-control" id="transition_cooldown" 
                                           name="transition_cooldown" value="{{ ad_frequency.transition_ad.cooldown_minutes|default:15 }}">
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="session_max_daily" class="form-label">会话开始广告每日最大次数</label>
                                    <input type="number" class="form-control" id="session_max_daily" 
                                           name="session_max_daily" value="{{ ad_frequency.session_start_ad.max_daily|default:2 }}">
                                </div>
                            </div>
                        </div>
                        
                        <!-- 会员策略 -->
                        <h5 class="section-title">用户策略</h5>
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="show_ads_to_anonymous" 
                                           name="show_ads_to_anonymous" {% if ads_display.show_ads_to_anonymous %}checked{% endif %}>
                                    <label class="form-check-label" for="show_ads_to_anonymous">向未登录用户展示广告</label>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="show_ads_to_free_users" 
                                           name="show_ads_to_free_users" {% if ads_display.show_ads_to_free_users %}checked{% endif %}>
                                    <label class="form-check-label" for="show_ads_to_free_users">向免费用户展示广告</label>
                                </div>
                            </div>
                            
                            <div class="col-12">
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle me-2"></i>
                                    会员用户将不会看到任何广告，这是会员的核心权益
                                </div>
                            </div>
                        </div>
                        
                        <!-- 提交按钮 -->
                        <div class="d-flex justify-content-end">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-1"></i> 保存配置
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 8.3 修改配置获取逻辑

修改广告服务处理函数，从数据库配置获取设置而非配置文件：

```python
def get_google_ads_settings():
    """获取Google广告配置"""
    from admin_panel.models import ConfigSettings
    
    # 获取基本配置
    enabled = ConfigSettings.get_config('google_adsense_enabled', 'false') == 'true'
    publisher_id = ConfigSettings.get_config('google_adsense_publisher_id', '')
    test_mode = ConfigSettings.get_config('google_adsense_test_mode', 'true') == 'true'
    
    # 获取广告单元配置
    ad_units_json = ConfigSettings.get_config('ad_units', '{}')
    ad_units = json.loads(ad_units_json) if isinstance(ad_units_json, str) else ad_units_json
    
    # 获取广告频率设置
    ad_frequency_json = ConfigSettings.get_config('ad_frequency_settings', '{}')
    ad_frequency = json.loads(ad_frequency_json) if isinstance(ad_frequency_json, str) else ad_frequency_json
    
    # 获取会员广告显示策略
    ads_display_json = ConfigSettings.get_config('ads_display_settings', '{}')
    ads_display = json.loads(ads_display_json) if isinstance(ads_display_json, str) else ads_display_json
    
    return {
        'google_adsense': {
            'enabled': enabled,
            'publisher_id': publisher_id,
            'test_mode': test_mode
        },
        'ad_units': ad_units,
        'ad_frequency': ad_frequency,
        'ads_display': ads_display
    }
```

### 8.4 添加后台菜单项

在`admin_panel/menu.py`中添加Google广告配置菜单项：

```python
# 在MENU_ITEMS字典中添加
'settings': [
    # 其他设置菜单...
    {
        'name': _('Google广告配置'),
        'url': 'admin_panel:google_ads_settings',
        'icon': 'fas fa-ad',
        'permission': 'admin_panel.setting_view',
    },
]
```

### 8.5 实现效果

通过后台管理系统实现的Google广告配置有以下优势：

1. **无需修改代码**: 管理员可以通过Web界面管理所有广告相关配置
2. **即时生效**: 配置变更即时生效，无需重启服务器
3. **权限控制**: 只有具有相应权限的管理员可以编辑广告配置
4. **操作日志**: 所有配置变更都会记录详细的操作日志
5. **适合非技术人员**: 友好的用户界面使非技术人员也能轻松管理

当广告收益数据、用户反馈或业务需求发生变化时，可以随时调整广告策略，无需开发人员介入。