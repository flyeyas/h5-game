# Google广告位置详细实施方案

本文档详细说明GameHub平台的广告位置布局和具体实现方法。

## 1. 全站通用广告位

### 1.1 顶部横幅广告

**位置描述**：
- 导航栏下方，主内容区域上方
- 在`templates/games/base.html`中插入

**实现代码**：
```html
<!-- 在base.html中的header和main之间 -->
{% if not is_member %}
<div class="container mt-3 mb-3">
    {% display_ad 'top_banner' %}
</div>
{% endif %}
```

**广告单元配置**：
- 尺寸：728x90（桌面）/ 320x50（移动）
- 响应式设置：是
- 广告单元ID：`top_banner_1`

### 1.2 底部横幅广告

**位置描述**：
- 主内容区域之后，页脚之前
- 在`templates/games/base.html`中插入

**实现代码**：
```html
<!-- 在base.html中的main和footer之间 -->
{% if not is_member %}
<div class="container mt-4 mb-3">
    {% display_ad 'bottom_banner' %}
</div>
{% endif %}
```

**广告单元配置**：
- 尺寸：728x90（桌面）/ 320x50（移动）
- 响应式设置：是
- 广告单元ID：`bottom_banner_1`

### 1.3 侧边栏广告

**位置描述**：
- 右侧边栏顶部和中部
- 在带有侧边栏的模板中插入

**实现代码**：
```html
<!-- 在带侧边栏的页面中 -->
{% if not is_member %}
<div class="sidebar-widget mb-4">
    <h4>赞助内容</h4>
    {% display_ad 'sidebar_top' %}
</div>

<div class="sidebar-widget mb-4 mt-5">
    {% display_ad 'sidebar_middle' %}
</div>
{% endif %}
```

**广告单元配置**：
- 尺寸：300x250（矩形）或 300x600（大型矩形）
- 响应式设置：否
- 广告单元ID：`sidebar_top_1` 和 `sidebar_middle_1`

## 2. 页面特定广告位

### 2.1 首页广告位

#### 2.1.1 热门游戏区域广告

**位置描述**：
- 热门游戏列表中第3和第8个位置插入
- 在`templates/games/home.html`中实现

**实现代码**：
```html
<!-- 在热门游戏列表中 -->
{% for game in hot_games %}
    {% if forloop.counter == 3 or forloop.counter == 8 %}
        {% if not is_member %}
        <div class="col-md-4 col-sm-6 mb-4 ad-container">
            <div class="card game-card">
                <div class="ad-label">广告</div>
                {% display_ad 'game_list_native' %}
            </div>
        </div>
        {% endif %}
    {% endif %}
    
    <div class="col-md-4 col-sm-6 mb-4">
        <!-- 游戏卡片内容 -->
    </div>
{% endfor %}
```

**广告单元配置**：
- 尺寸：与游戏卡片相同（响应式）
- 广告类型：信息流原生广告
- 广告单元ID：`game_list_native_1`

#### 2.1.2 推荐游戏区域广告

**位置描述**：
- 推荐游戏列表之后
- 在首页推荐区域下方

**实现代码**：
```html
<!-- 在推荐游戏列表后 -->
{% if not is_member %}
<div class="row mt-4 mb-5">
    <div class="col-12">
        {% display_ad 'home_recommended_banner' %}
    </div>
</div>
{% endif %}
```

**广告单元配置**：
- 尺寸：970x250（桌面）/ 300x250（移动）
- 响应式设置：是
- 广告单元ID：`home_recommended_1`

### 2.2 游戏详情页广告位

#### 2.2.1 游戏信息下方广告

**位置描述**：
- 游戏描述和特性列表之后，评论区之前
- 在`templates/games/game_detail.html`中实现

**实现代码**：
```html
<!-- 游戏描述后，评论区前 -->
{% if not is_member %}
<div class="game-ad-container my-4">
    {% display_ad 'game_detail_info' %}
</div>
{% endif %}
```

**广告单元配置**：
- 尺寸：728x90（桌面）/ 300x250（移动）
- 响应式设置：是
- 广告单元ID：`game_detail_1`

#### 2.2.2 游戏加载前广告（iframe实施方案）

**位置描述**：
- 在用户点击"开始游戏"后，iframe加载游戏URL前
- 实现为插页式广告

**实现代码**：
```html
<!-- 在游戏详情页添加游戏加载前广告容器 -->
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

<!-- 游戏容器 -->
<div class="game-container">
    <button id="start-game-button" class="btn btn-primary mb-3">开始游戏</button>
    <div class="game-frame-container">
        <iframe id="game-frame" data-game-url="{{ game.url }}" frameborder="0" scrolling="no" width="100%" height="600"></iframe>
    </div>
</div>
```

**JavaScript实现**：
```javascript
// 游戏加载前广告实现
document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('start-game-button');
    const gameFrame = document.getElementById('game-frame');
    const adContainer = document.getElementById('pre-game-ad-container');
    const skipButton = document.getElementById('skip-ad-button');
    const countdownElement = document.getElementById('ad-countdown');
    
    // 检查是否为会员
    const isMember = document.body.dataset.isMember === 'true';
    
    // 游戏加载函数
    function loadGame() {
        const gameUrl = gameFrame.getAttribute('data-game-url');
        gameFrame.src = gameUrl;
        
        // 显示游戏框架
        gameFrame.style.display = 'block';
        
        // 隐藏开始按钮
        startButton.style.display = 'none';
    }
    
    // 显示广告计时器
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
    }
    
    // 开始游戏按钮点击处理
    startButton.addEventListener('click', function() {
        if (isMember) {
            // 会员用户直接加载游戏
            loadGame();
        } else {
            // 非会员用户显示广告
            adContainer.style.display = 'flex';
            
            // 开始广告计时
            startAdCountdown();
            
            // 广告加载
            (adsbygoogle = window.adsbygoogle || []).push({
                adSlot: "pre_game_interstitial_1"
            });
            
            // 跳过广告按钮点击事件
            skipButton.addEventListener('click', function() {
                adContainer.style.display = 'none';
                loadGame();
            });
            
            // 设置广告超时（如果广告加载失败）
            setTimeout(function() {
                if (gameFrame.src === '') {
                    adContainer.style.display = 'none';
                    loadGame();
                }
            }, 10000); // 10秒后超时
        }
    });
});
```

**CSS样式**：
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
}

/* 游戏容器样式 */
.game-container {
    margin: 20px 0;
    text-align: center;
}

.game-frame-container {
    position: relative;
    width: 100%;
    overflow: hidden;
    border: 1px solid #ddd;
    border-radius: 4px;
}

/* 适配移动设备 */
@media (max-width: 768px) {
    .ad-wrapper {
        padding: 15px;
    }
    
    .ad-content {
        min-height: 200px;
    }
    
    .game-frame-container {
        height: 400px;
    }
}
```

**广告单元配置**：
- 类型：插页式广告
- 尺寸：300x250 或 336x280
- 广告单元ID：`pre_game_interstitial_1`

### 2.3 游戏分类页广告位

#### 2.3.1 分类标题下方广告

**位置描述**：
- 分类描述之后，游戏列表之前
- 在`templates/games/category_detail.html`中实现

**实现代码**：
```html
<!-- 分类描述之后 -->
{% if not is_member %}
<div class="category-banner-ad my-4">
    {% display_ad 'category_banner' %}
</div>
{% endif %}
```

**广告单元配置**：
- 尺寸：728x90
- 响应式设置：是
- 广告单元ID：`category_banner_1`

#### 2.3.2 游戏列表内广告

**位置描述**：
- 分类游戏列表中，每8个游戏后插入广告
- 在游戏列表渲染循环中实现

**实现代码**：
```html
<!-- 在分类游戏列表中 -->
{% for game in category_games %}
    {% if forloop.counter|divisibleby:8 and not is_member %}
    <div class="col-md-4 col-sm-6 mb-4">
        <div class="card game-card ad-card">
            <div class="ad-tag">广告</div>
            {% display_ad 'category_list_native' %}
        </div>
    </div>
    {% endif %}
    
    <div class="col-md-4 col-sm-6 mb-4">
        <!-- 游戏卡片内容 -->
    </div>
{% endfor %}
```

**广告单元配置**：
- 尺寸：与游戏卡片相同（响应式）
- 广告类型：信息流原生广告
- 广告单元ID：`category_list_native_1`

### 2.4 搜索结果页广告位

#### 2.4.1 搜索结果顶部广告

**位置描述**：
- 搜索条件/筛选器下方，结果列表之前
- 在`templates/games/search.html`中实现

**实现代码**：
```html
<!-- 搜索筛选器后，结果列表前 -->
{% if not is_member %}
<div class="search-result-ad my-3">
    {% display_ad 'search_top_banner' %}
</div>
{% endif %}
```

**广告单元配置**：
- 尺寸：728x90（桌面）/ 300x250（移动）
- 响应式设置：是
- 广告单元ID：`search_top_1`

#### 2.4.2 搜索结果列表内广告

**位置描述**：
- 搜索结果列表中，第3、第10、第20位
- 在搜索结果渲染循环中实现

**实现代码**：
```html
<!-- 在搜索结果列表中 -->
{% for game in search_results %}
    {% if forloop.counter == 3 or forloop.counter == 10 or forloop.counter == 20 %}
        {% if not is_member %}
        <div class="search-result-item ad-item">
            <div class="ad-label">广告</div>
            {% display_ad 'search_result_native' %}
        </div>
        {% endif %}
    {% endif %}
    
    <div class="search-result-item">
        <!-- 搜索结果条目内容 -->
    </div>
{% endfor %}
```

**广告单元配置**：
- 尺寸：与搜索结果条目相同
- 广告类型：信息流原生广告
- 广告单元ID：`search_result_native_1`

## 3. 广告单元ID命名规范

为了便于管理和统计，广告单元ID应遵循以下命名规范：

```
[页面类型]_[位置]_[序号]
```

示例：
- `home_top_1`：首页顶部广告1号
- `game_detail_1`：游戏详情页广告1号
- `category_banner_1`：分类页横幅广告1号
- `search_result_native_1`：搜索结果页原生广告1号
- `pre_game_interstitial_1`：游戏加载前插页式广告1号

## 4. 移动设备适配

为确保移动端良好的广告展示效果，应采取以下措施：

1. **响应式广告单元设置**：
   - 使用Google AdSense的响应式广告单元
   - 为移动端提供更小尺寸的广告

2. **移动端广告数量控制**：
   - 在移动端减少每个页面的广告数量
   - 移除部分仅桌面显示的广告位

3. **广告位置调整**：
   - 在小屏幕上重新排列广告位置
   - 使用媒体查询为不同设备提供不同样式

**实现示例**：
```css
/* 移动端广告样式调整 */
@media (max-width: 768px) {
    .sidebar-ad {
        display: none; /* 在移动端隐藏侧边栏广告 */
    }
    
    .game-list-ad {
        margin: 15px 0; /* 调整移动端游戏列表广告间距 */
    }
    
    .interstitial-ad-container {
        padding: 10px; /* 减小插页式广告内边距 */
    }
}
```

## 5. 会员用户广告处理

对于会员用户，系统应完全隐藏所有广告位。实现逻辑如下：

1. **服务器端检查**：
   - 在渲染模板前检查用户会员状态
   - 会员用户的模板中不包含任何广告代码

2. **会员状态缓存**：
   - 将会员状态存储在会话中，避免频繁数据库查询
   - 设置合理的缓存过期时间（如1小时）

3. **前端广告控制**：
   - 在页面加载时，通过JavaScript检查会员状态
   - 会员用户不执行任何广告加载代码

**JavaScript实现示例**：
```javascript
// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 从页面数据属性获取会员状态
    const isMember = document.body.dataset.isMember === 'true';
    
    // 非会员用户才初始化广告
    if (!isMember) {
        initializeAds();
    } else {
        // 会员用户隐藏所有广告占位符
        document.querySelectorAll('.ad-container').forEach(container => {
            container.style.display = 'none';
        });
    }
});
```

## 6. 广告样式与用户体验优化

为了提高广告与网站的整合度，同时保持良好的用户体验，应遵循以下原则：

1. **广告标识清晰**：
   - 所有广告位都应有明确的"广告"标识
   - 使用一致的样式区分广告和内容

2. **广告容器样式优化**：
   - 统一广告容器样式，与网站设计协调
   - 为广告添加适当的边距和边框

3. **延迟加载优化**：
   - 使用延迟加载技术，优先加载页面内容
   - 仅当广告容器进入视口时才加载广告

4. **广告频率限制**：
   - 对游戏加载前广告设置合理的展示频率
   - 例如，同一用户在30分钟内只展示一次游戏加载前广告

**CSS样式示例**：
```css
/* 广告容器通用样式 */
.ad-container {
    position: relative;
    background-color: #f9f9f9;
    border: 1px solid #eee;
    border-radius: 4px;
    overflow: hidden;
    text-align: center;
}

/* 广告标识样式 */
.ad-label {
    position: absolute;
    top: 2px;
    left: 2px;
    background-color: rgba(0,0,0,0.5);
    color: white;
    font-size: 10px;
    padding: 2px 4px;
    border-radius: 2px;
    z-index: 10;
}

/* 信息流广告样式 */
.ad-card {
    height: 100%;
    display: flex;
    flex-direction: column;
}
``` 