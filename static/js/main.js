/**
 * HTML5游戏平台的主要JavaScript文件
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化图片懒加载
    // lazyLoadImages();
    
    // 添加反馈表单处理
    // setupFeedbackForm();
    
    // 初始化轮播图
    // initializeCarousels();
    
    // 先存储用户信息，再检查登录状态
    storeUserInfo();
    checkLoginStatus();
    
    // 设置CSRF令牌到AJAX请求
    setupCsrfAjax();
    
    // 设置登出处理
    setupLogoutHandlers();
    
    // 每5秒检查一次登录状态
    setInterval(checkLoginStatus, 5000);
});

/**
 * 导航栏滚动效果
 */
function handleNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
}

/**
 * 游戏卡片悬停效果
 */
function setupGameCardHover() {
    const gameCards = document.querySelectorAll('.game-card');
    
    gameCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        });
    });
}

/**
 * 回到顶部按钮
 */
function setupBackToTop() {
    const backToTopBtn = document.querySelector('.back-to-top');
    if (!backToTopBtn) return;
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            backToTopBtn.classList.add('show');
        } else {
            backToTopBtn.classList.remove('show');
        }
    });
    
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * 游戏加载动画
 */
function setupGameLoading() {
    const gameIframe = document.querySelector('.game-iframe');
    const loadingElement = document.querySelector('.game-loading');
    
    if (!gameIframe || !loadingElement) return;
    
    gameIframe.addEventListener('load', function() {
        loadingElement.style.display = 'none';
    });
}

/**
 * 评分系统
 */
function setupRatingSystem() {
    const ratingInputs = document.querySelectorAll('.star-rating input');
    if (ratingInputs.length === 0) return;
    
    ratingInputs.forEach(input => {
        input.addEventListener('change', function() {
            const rating = this.value;
            const gameId = this.getAttribute('data-game-id');
            
            // 这里可以添加AJAX请求将评分发送到服务器
            console.log(`Game ${gameId} rated ${rating} stars`);
            
            // 显示感谢消息
            const ratingContainer = this.closest('.rating-container');
            if (ratingContainer) {
                const thankMessage = document.createElement('div');
                thankMessage.className = 'alert alert-success mt-2';
                thankMessage.textContent = '谢谢您的评分！';
                ratingContainer.appendChild(thankMessage);
                
                // 3秒后移除消息
                setTimeout(() => {
                    thankMessage.remove();
                }, 3000);
            }
        });
    });
}

/**
 * 搜索功能
 */
function setupSearch() {
    const searchForm = document.querySelector('#search-form');
    const searchInput = document.querySelector('#search-input');
    
    if (!searchForm || !searchInput) return;
    
    searchForm.addEventListener('submit', function(e) {
        if (searchInput.value.trim() === '') {
            e.preventDefault();
            searchInput.classList.add('is-invalid');
            
            // 添加提示
            let feedback = searchInput.nextElementSibling;
            if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = '请输入搜索关键词';
                searchInput.after(feedback);
            }
        } else {
            searchInput.classList.remove('is-invalid');
        }
    });
    
    // 实时搜索建议（可选功能）
    searchInput.addEventListener('input', function() {
        if (this.value.length >= 2) {
            // 这里可以添加AJAX请求获取搜索建议
            // 示例代码，实际实现需要后端API支持
            console.log(`Searching for: ${this.value}`);
        }
    });
}

/**
 * 移动端导航菜单
 */
function setupMobileNav() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (!navbarToggler || !navbarCollapse) return;
    
    // 点击导航链接后自动关闭菜单
    const navLinks = navbarCollapse.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992) { // Bootstrap的lg断点
                navbarToggler.click();
            }
        });
    });
}

/**
 * 收藏游戏功能
 */
function toggleFavorite(button, gameId) {
    // 检查用户是否登录，若未登录则跳转到登录页面
    if (!isUserLoggedIn(true, window.location.pathname)) {
        window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
        return;
    }
    
    // 禁用按钮防止重复点击
    button.disabled = true;
    
    // 准备请求数据
    const formData = new FormData();
    formData.append('game_id', gameId);
    
    // 发送请求
    fetch('/api/favorite/toggle/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 403) {
                window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
                return Promise.reject('需要登录');
            }
            return Promise.reject('请求失败: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        console.log('收藏响应:', data);
        button.disabled = false;
        
        if (data.success) {
            // 显示成功消息
            showToast(data.message, 'success');
            
            // 更新按钮状态
            const icon = button.querySelector('i');
            const text = button.querySelector('span');
            
            if (data.data.is_favorite) {
                button.classList.add('active', 'favorited');
                button.classList.remove('not-favorited');
                if (icon) icon.className = 'fas fa-heart';
                if (text) text.textContent = '已收藏';
            } else {
                button.classList.remove('active', 'favorited');
                button.classList.add('not-favorited');
                if (icon) icon.className = 'far fa-heart';
                if (text) text.textContent = '收藏';
            }
        } else {
            // 显示错误消息
            showToast(data.message, 'danger');
            
            // 检查是否需要重定向
            if (data.redirect_url) {
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1500);
            }
        }
    })
    .catch(error => {
        console.error('收藏请求错误:', error);
        button.disabled = false;
        showToast('操作失败，请稍后再试', 'danger');
    });
}

/**
 * 检查用户是否已登录
 * 使用Django默认会话检查机制
 */
function isUserLoggedIn() {
    // 检查是否有会话cookie
    if (document.cookie.indexOf('sessionid=') !== -1) {
        console.log('用户已登录: 发现sessionid cookie');
        return true;
    }
    
    // 检查localStorage
    if (localStorage.getItem('user_id')) {
        console.log('用户已登录: 发现localStorage中的user_id');
        return true;
    }
    
    console.log('用户未登录: 没有找到会话标识');
    return false;
}

/**
 * 全屏模式切换
 */
function toggleFullScreen(gameContainer) {
    if (!document.fullscreenElement) {
        gameContainer.requestFullscreen().catch(err => {
            console.error(`Error attempting to enable full-screen mode: ${err.message}`);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

/**
 * 语言切换
 */
function changeLanguage(selectElement) {
    const language = selectElement.value;
    // 设置cookie或本地存储
    document.cookie = `language=${language}; path=/; max-age=31536000`;
    // 刷新页面应用新语言
    window.location.reload();
}

/**
 * 通用API请求函数
 * @param {Object} options - 请求配置
 * @param {string} options.url - 请求URL
 * @param {string} options.method - 请求方法，默认为'GET'
 * @param {Object|FormData} options.data - 请求数据
 * @param {Function} options.success - 成功回调函数
 * @param {Function} options.error - 错误回调函数
 * @param {boolean} options.showToast - 是否自动显示提示，默认为true
 * @param {boolean} options.redirect - 是否自动处理重定向，默认为true
 * @param {boolean} options.useFormData - 是否使用FormData对象发送数据，默认为false
 */
function apiRequest(options) {
    const defaults = {
        method: 'GET',
        data: null,
        success: null,
        error: null,
        showToast: true,
        redirect: true,
        useFormData: false,
        headers: {}
    };

    const settings = Object.assign({}, defaults, options);
    const isFormData = settings.useFormData || settings.data instanceof FormData;
    const isGet = settings.method.toUpperCase() === 'GET';

    // 创建XHR对象
    const xhr = new XMLHttpRequest();
    
    // 处理GET请求参数
    let url = settings.url;
    if (isGet && settings.data) {
        const params = new URLSearchParams();
        for (const key in settings.data) {
            if (settings.data.hasOwnProperty(key)) {
                params.append(key, settings.data[key]);
            }
        }
        url += (url.includes('?') ? '&' : '?') + params.toString();
    }
    
    // 打开连接
    xhr.open(settings.method, url, true);
    
    // 设置请求头
    if (!isFormData && !isGet) {
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    }
    
    // 添加CSRF令牌
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
    }
    
    // 添加自定义请求头
    for (const key in settings.headers) {
        if (settings.headers.hasOwnProperty(key)) {
            xhr.setRequestHeader(key, settings.headers[key]);
        }
    }

    // 如果需要加入onComplete回调
    const completeCallback = settings.onComplete;
    
    // 响应处理
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            // 如果有完成回调，调用它
            if (completeCallback) {
                completeCallback();
            }
            
            // 请求完成但状态码不是成功
            if (xhr.status < 200 || xhr.status >= 300) {
                console.error('请求失败:', xhr.status, xhr.statusText);
                if (settings.showToast) {
                    showToast('请求失败: ' + xhr.statusText, 'error');
                }
                if (settings.error) {
                    settings.error({
                        success: false,
                        message: '请求失败: ' + xhr.statusText,
                        code: 'http_error',
                        status: xhr.status
                    });
                }
                return;
            }
            
            let response;
            
            try {
                response = JSON.parse(xhr.responseText);
            } catch (e) {
                console.error('解析响应失败:', e);
                if (settings.showToast) {
                    showToast('服务器响应格式错误', 'error');
                }
                if (settings.error) {
                    settings.error({
                        success: false,
                        message: '服务器响应格式错误',
                        code: 'internal_error'
                    });
                }
                return;
            }
            
            // 处理业务状态码
            if (response.success) {
                // 成功状态
                if (settings.showToast && response.message) {
                    showToast(response.message, 'success');
                }
                
                if (settings.success) {
                    settings.success(response);
                }
            } else {
                // 失败状态，根据业务状态码处理
                const isLoginRequired = response.code === 'login_required';
                const isGameDetailPage = window.location.pathname.includes('/games/');
                
                // 处理特定业务状态码 - 登录需求
                if (isLoginRequired) {
                    // 游戏详情页不自动跳转，只提示用户
                    if (isGameDetailPage && !settings.redirect) {
                        // 只显示一次提示
                        showToast('请先登录后再操作', 'error');
                    } 
                    // 其他页面保持原有逻辑，需要登录时跳转
                    else if (settings.redirect) {
                        // 显示错误消息，然后跳转
                        if (settings.showToast && response.message) {
                            showToast(response.message, 'error');
                        }
                        setTimeout(function() {
                            window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                        }, 1500);
                    }
                } 
                // 其他错误类型
                else if (settings.showToast && response.message) {
                    showToast(response.message, 'error');
                }
                
                if (settings.error) {
                    settings.error(response);
                }
            }
        }
    };
    
    // 网络错误处理
    xhr.onerror = function() {
        console.error('网络请求失败');
        if (settings.showToast) {
            showToast('网络连接失败，请检查网络设置', 'error');
        }
        if (settings.error) {
            settings.error({
                success: false,
                message: '网络连接失败',
                code: 'network_error'
            });
        }
    };
    
    // 发送请求
    if (isGet || !settings.data) {
        xhr.send();
    } else if (isFormData) {
        xhr.send(settings.data);
    } else {
        const params = new URLSearchParams();
        for (const key in settings.data) {
            if (settings.data.hasOwnProperty(key)) {
                params.append(key, settings.data[key]);
            }
        }
        xhr.send(params.toString());
    }
    
    return xhr;
}

/**
 * 从cookie中获取指定名称的值
 * @param {string} name - cookie名称
 * @returns {string|null} cookie值，如果不存在则返回null
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // 查找以name=开头的cookie字符串
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * 获取CSRF令牌
 * 先尝试从cookie获取，再尝试从页面上的csrfmiddlewaretoken输入框获取
 */
function getCsrfToken() {
    // 从cookie获取
    const csrfCookie = getCookie('csrftoken');
    if (csrfCookie) {
        return csrfCookie;
    }
    
    // 从表单输入获取
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
        return csrfInput.value;
    }
    
    return null;
}

$(document).ready(function() {
    // 导航下拉菜单悬停效果
    $('.dropdown').hover(
        function() {
            $(this).find('.dropdown-menu').stop(true, true).delay(200).fadeIn(300);
        },
        function() {
            $(this).find('.dropdown-menu').stop(true, true).delay(200).fadeOut(300);
        }
    );
    
    // 游戏卡片交互效果
    $('.game-card').hover(
        function() {
            $(this).find('.btn-primary').addClass('btn-success').removeClass('btn-primary');
        },
        function() {
            $(this).find('.btn-success').addClass('btn-primary').removeClass('btn-success');
        }
    );
    
    // 分类卡片交互效果
    $('.category-card').hover(
        function() {
            $(this).find('.btn-outline-primary').removeClass('btn-outline-primary').addClass('btn-primary');
        },
        function() {
            $(this).find('.btn-primary').removeClass('btn-primary').addClass('btn-outline-primary');
        }
    );
    
    // 搜索表单提交前验证
    $('.search-form').on('submit', function(e) {
        var searchValue = $(this).find('input[type="search"]').val().trim();
        if (searchValue === '') {
            e.preventDefault();
            return false;
        }
    });
    
    // 收藏按钮交互 - 只在非用户主页页面绑定此事件
    if (!window.location.pathname.includes('/profile/')) {
        $('.favorite-btn').not('#favorite-btn').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            var gameId = $this.data('game-id');
            
            // 禁用按钮防止重复点击
            $this.prop('disabled', true);
            
            // 准备请求数据
            const formData = new FormData();
            formData.append('game_id', gameId);
            
            // 使用新的API端点发送请求
            fetch('/api/favorite/toggle/', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 403) {
                        window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
                        return Promise.reject('需要登录');
                    }
                    return Promise.reject('请求失败: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('收藏响应:', data);
                $this.prop('disabled', false);
                
                if (data.success) {
                    // 显示成功消息
                    showToast(data.message, 'success');
                    
                    // 更新按钮状态
                    if (data.data.is_favorite) {
                        $this.addClass('text-danger').removeClass('text-secondary');
                        $this.find('i').removeClass('far').addClass('fas');
                    } else {
                        $this.removeClass('text-danger').addClass('text-secondary');
                        $this.find('i').removeClass('fas').addClass('far');
                    }
                } else {
                    // 显示错误消息
                    showToast(data.message, 'danger');
                    
                    // 检查是否需要重定向
                    if (data.redirect_url) {
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 1500);
                    }
                }
            })
            .catch(error => {
                console.error('收藏请求错误:', error);
                $this.prop('disabled', false);
                showToast('操作失败，请稍后再试', 'danger');
            });
        });
    }
    
    // 评分功能初始化
    if ($('.rating-input').length) {
        $('.rating-input i').on('click', function() {
            var $this = $(this);
            var value = $this.data('rating');
            $('#id_rating').val(value);
            
            // 更新星星显示
            $('.rating-input i').each(function() {
                if ($(this).data('rating') <= value) {
                    $(this).removeClass('far').addClass('fas');
                } else {
                    $(this).removeClass('fas').addClass('far');
                }
            });
        });
    }
    
    // 筛选功能 - 应用筛选条件
    $('.filter-form input, .filter-form select').on('change', function() {
        $(this).closest('form').submit();
    });
    
    // 排序下拉选项交互
    $('.sort-dropdown .dropdown-item').on('click', function(e) {
        e.preventDefault();
        var $this = $(this);
        var sort = $this.data('sort');
        
        // 更新隐藏字段值
        $('#sort-field').val(sort);
        
        // 更新显示文本
        $('.sort-text').text($this.text());
        
        // 提交表单
        $('#filter-sort-form').submit();
    });
    
    // 移动端菜单按钮点击效果
    $('.navbar-toggler').on('click', function() {
        $(this).toggleClass('active');
    });
    
    // 图片懒加载初始化
    if ('loading' in HTMLImageElement.prototype) {
        // 浏览器支持原生懒加载
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        // 浏览器不支持原生懒加载，可以使用懒加载库
        // 这里可以添加第三方懒加载库的初始化代码
    }
    
    // 游戏分类页面的筛选功能
    $('.game-categories-page .form-check-input').on('change', function() {
        console.log('筛选条件已更改');
        // 在实际项目中，这里可以添加AJAX请求或表单提交来应用筛选
    });
});

/**
 * 从页面DOM中获取并存储用户信息
 * 在页面加载时调用，确保用户状态正确存储
 */
function storeUserInfo() {
    // 从页面中查找用户信息
    const userInfoElement = document.querySelector('meta[name="user-info"]');
    if (userInfoElement) {
        try {
            const userInfo = JSON.parse(userInfoElement.getAttribute('content'));
            if (userInfo && userInfo.id) {
                localStorage.setItem('user_id', userInfo.id);
                localStorage.setItem('username', userInfo.username || '');
                console.log('用户信息已存储到localStorage', userInfo);
            }
        } catch (e) {
            console.error('解析用户信息失败', e);
        }
    } else {
        console.log('未找到用户信息meta标签');
    }
    
    // 从cookie中获取会话ID
    const frontSessionCookie = getCookie('front_session');
    if (frontSessionCookie) {
        localStorage.setItem('front_session_exists', 'true');
        console.log('前台会话Cookie存在:', frontSessionCookie.substring(0, 5) + '...');
    } else {
        localStorage.removeItem('front_session_exists');
        console.log('前台会话Cookie不存在');
    }
}

/**
 * 检查用户登录状态
 * 用于页面加载时检查用户是否已登录
 */
function checkLoginStatus() {
    // 获取需要登录才能访问的元素
    const authRequiredElements = document.querySelectorAll('.auth-required');
    
    // 检查用户是否已登录
    const isLoggedIn = isUserLoggedIn();
    
    // 处理需要身份验证的元素
    authRequiredElements.forEach(element => {
        if (isLoggedIn) {
            // 用户已登录，显示元素
            element.classList.remove('d-none');
        } else {
            // 用户未登录，隐藏元素并可能显示登录提示
            element.classList.add('d-none');
            
            // 如果元素有data-login-message属性，则显示提示信息
            const loginMessage = element.getAttribute('data-login-message');
            if (loginMessage && element.parentNode) {
                const messageElement = document.createElement('div');
                messageElement.className = 'login-prompt';
                messageElement.innerHTML = `<a href="/login?next=${encodeURIComponent(window.location.pathname)}">${loginMessage}</a>`;
                element.parentNode.insertBefore(messageElement, element);
            }
        }
    });
    
    // 获取需要根据登录状态切换显示的元素
    const loginToggleElements = document.querySelectorAll('[data-login-toggle]');
    
    // 根据登录状态切换显示
    loginToggleElements.forEach(element => {
        const showWhen = element.getAttribute('data-login-toggle');
        if ((showWhen === 'logged-in' && isLoggedIn) || 
            (showWhen === 'logged-out' && !isLoggedIn)) {
            element.classList.remove('d-none');
        } else {
            element.classList.add('d-none');
        }
    });
}

/**
 * 重定向到用户个人主页
 */
function redirectToProfile() {
    window.location.href = '/profile/';
}

/**
 * 游戏分类折叠功能
 */
function setupCategoryCollapse() {
    const categoryCollapseButton = document.querySelector('[data-bs-target="#categoriesCollapse"]');
    if (!categoryCollapseButton) return;
    
    const buttonText = categoryCollapseButton.querySelector('span');
    const buttonIcon = categoryCollapseButton.querySelector('i');
    
    // 监听折叠状态变化
    document.getElementById('categoriesCollapse').addEventListener('show.bs.collapse', function() {
        buttonIcon.classList.remove('fa-chevron-down');
        buttonIcon.classList.add('fa-chevron-up');
        if (buttonText) buttonText.textContent = '收起';
    });
    
    document.getElementById('categoriesCollapse').addEventListener('hide.bs.collapse', function() {
        buttonIcon.classList.remove('fa-chevron-up');
        buttonIcon.classList.add('fa-chevron-down');
        if (buttonText) buttonText.textContent = '显示更多';
    });
    
    // 如果分类总数少于或等于6个，隐藏折叠按钮
    const firstRowCategoryCount = document.querySelectorAll('.category-first-row .col-6').length;
    const collapseCategoryCount = document.querySelectorAll('#categoriesCollapse .col-6').length;
    
    if (collapseCategoryCount === 0) {
        categoryCollapseButton.style.display = 'none';
    }
}

// CSRF令牌管理
function getCsrfToken() {
    // 获取隐藏的CSRF token字段
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        return csrfInput.value;
    }
    // 尝试从cookie获取
    const cookies = document.cookie.split(';');
    const csrfCookie = cookies.find(cookie => cookie.trim().startsWith('csrftoken='));
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    return null;
}

// 设置CSRF令牌到AJAX请求头
function setupCsrfAjax() {
    // 拦截所有jQuery AJAX请求
    if (typeof $ !== 'undefined' && $.ajaxSetup) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                // 只处理非GET请求
                if (settings.type !== 'GET') {
                    const token = getCsrfToken();
                    if (token) {
                        // 设置CSRF令牌到请求头
                        xhr.setRequestHeader('X-CSRFToken', token);
                    }
                }
            }
        });
    }
    
    // 拦截所有fetch请求
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // 只处理非GET请求
        if (options.method && options.method !== 'GET') {
            const token = getCsrfToken();
            if (token) {
                // 确保headers存在
                options.headers = options.headers || {};
                
                // 如果headers是Headers对象，使用append方法
                if (options.headers instanceof Headers) {
                    options.headers.append('X-CSRFToken', token);
                } else {
                    // 否则，作为普通对象处理
                    options.headers['X-CSRFToken'] = token;
                }
            }
        }
        
        return originalFetch(url, options);
    };
}

/**
 * 清除用户会话数据
 * 用于用户登出时清除所有相关的会话信息
 */
function clearUserSession() {
    // 清除localStorage中的用户数据
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('front_session_exists');
    
    // 清除sessionStorage中的数据
    sessionStorage.removeItem('user_id');
    sessionStorage.removeItem('username');
    
    console.log('已清除用户会话数据');
}

/**
 * 处理登出操作
 * 为登出链接添加事件监听，确保正确清除会话
 */
function setupLogoutHandlers() {
    // 获取所有登出链接
    const logoutLinks = document.querySelectorAll('a[href*="logout"]');
    
    logoutLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 不阻止默认行为，让链接正常导航到登出URL
            
            // 清除本地存储的用户数据
            clearUserSession();
            
            console.log('用户点击登出链接，已清除本地会话数据');
        });
    });
} 