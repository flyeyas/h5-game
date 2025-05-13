/**
 * 太空冒险游戏详情页面JavaScript功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化游戏加载
    initGameLoading();
    
    // 初始化评论系统
    initCommentSystem();
    
    // 初始化评分系统
    initRatingSystem();
    
    // 初始化全屏功能
    initFullscreenButton();
    
    // 初始化收藏功能
    initFavoriteButton();
    
    // 初始化分享功能
    initShareButton();
    
    // 初始化游戏卡片悬停效果
    initGameCards();
    
    // 初始化游戏卡片AJAX加载
    initGameCardLinks();
    
    // 初始化浏览器导航事件处理
    initBrowserNavigation();
});

/**
 * 通过游戏ID加载游戏详情
 * @param {number} gameId - 游戏ID
 * @param {function} callback - 回调函数，处理加载完成后的操作
 */
function loadGameById(gameId, callback) {
    // 检查gameId是否有效
    if (!gameId) {
        showMessage('游戏ID无效', 'danger');
        return;
    }
    
    // 先从当前URL获取游戏数据，如果已经有，则不需要再请求
    const currentGameId = document.querySelector('[data-game-id]')?.getAttribute('data-game-id');
    if (currentGameId && parseInt(currentGameId) === parseInt(gameId)) {
        if (typeof callback === 'function') {
            callback(null, { success: true, isCurrentGame: true });
        }
        return;
    }
    
    // 显示加载中状态
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-overlay';
    loadingIndicator.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
    document.body.appendChild(loadingIndicator);
    
    // 使用Fetch API获取游戏详情
    fetch(`/game/${gameId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应错误');
            }
            return response.text();
        })
        .then(html => {
            // 更新页面URL
            window.history.pushState({gameId: gameId}, '', `/game/${gameId}/`);
            
            // 更新页面内容
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // 获取主要内容区域
            const mainContent = doc.querySelector('#main-content') || doc.querySelector('main');
            if (mainContent) {
                document.querySelector('#main-content').innerHTML = mainContent.innerHTML;
                
                // 更新页面标题
                document.title = doc.title;
                
                // 更新页面其他相关内容
                const heroSection = doc.querySelector('.hero-section');
                if (heroSection) {
                    document.querySelector('.hero-section').innerHTML = heroSection.innerHTML;
                }
                
                // 重新初始化页面组件，但移除已经初始化过的元素的初始化标记
                // 这样可以确保它们在初始化函数中会被重新初始化
                document.querySelectorAll('[data-initialized="true"]').forEach(el => {
                    el.setAttribute('data-initialized', 'false');
                });
                
                // 重新初始化页面组件
                initGameLoading();
                initCommentSystem();
                initRatingSystem();
                initFullscreenButton();
                initFavoriteButton();
                initShareButton();
                initGameCards();
                
                // 执行回调
                if (typeof callback === 'function') {
                    callback(null, { success: true });
                }
            } else {
                throw new Error('无法解析页面内容');
            }
        })
        .catch(error => {
            console.error('获取游戏详情失败:', error);
            showMessage('获取游戏详情失败，请稍后重试', 'danger');
            
            // 执行回调
            if (typeof callback === 'function') {
                callback(error, { success: false });
            }
        })
        .finally(() => {
            // 移除加载指示器
            document.body.removeChild(loadingIndicator);
        });
}

/**
 * 使用jQuery AJAX加载游戏详情
 * 对于不支持fetch API的浏览器，提供jQuery版本的AJAX请求
 */
function loadGameDetailAjax(gameId, callback) {
    if (!gameId) {
        showMessage('游戏ID无效', 'danger');
        return;
    }
    
    // 显示加载中状态
    const loadingIndicator = $('<div class="loading-overlay"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>');
    $('body').append(loadingIndicator);
    
    // 使用jQuery的AJAX请求API
    $.ajax({
        url: `/api/game/${gameId}/`,
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            if (!data.success) {
                throw new Error(data.error || '请求失败');
            }
            
            // 更新游戏标题
            document.title = data.game.title + ' - GameHub';
            
            // 更新页面URL
            window.history.pushState({gameId: gameId}, '', `/game/${gameId}/`);
            
            // 更新游戏详情内容
            updateGameDetailContent(data);
            
            // 执行回调
            if (typeof callback === 'function') {
                callback(null, { success: true });
            }
        },
        error: function(xhr, status, error) {
            console.error('获取游戏详情失败:', error);
            showMessage('获取游戏详情失败，请稍后重试', 'danger');
            
            // 执行回调
            if (typeof callback === 'function') {
                callback(error, { success: false });
            }
        },
        complete: function() {
            // 移除加载指示器
            loadingIndicator.remove();
        }
    });
}

/**
 * 更新游戏详情内容
 * @param {Object} data - 游戏详情数据
 */
function updateGameDetailContent(data) {
    const game = data.game;
    
    // 更新游戏标题和描述
    $('.hero-section h1').text(game.title);
    $('.hero-section p').text(game.description);
    
    // 更新评分
    updateRatingDisplay(game.rating, data.comments.length);
    
    // 更新游戏缩略图
    $('.hero-section img').attr('src', game.thumbnail_url);
    
    // 更新收藏按钮状态
    const favoriteBtn = $('.favorite-btn');
    if (data.is_favorite) {
        favoriteBtn.removeClass('btn-outline-light').addClass('btn-danger');
        favoriteBtn.find('i').removeClass('fa-heart-o').addClass('fa-heart');
    } else {
        favoriteBtn.removeClass('btn-danger').addClass('btn-outline-light');
        favoriteBtn.find('i').removeClass('fa-heart').addClass('fa-heart-o');
    }
    favoriteBtn.attr('data-game-id', game.id);
    
    // 更新游戏iframe
    $('.game-iframe').attr('src', game.iframe_url);
    
    // 更新游戏信息
    $('.game-play-count').text(game.play_count);
    $('.game-created-at').text(game.created_at);
    
    // 更新游戏描述
    $('#description p').html(game.description.replace(/\n/g, '<br>'));
    
    // 更新游戏分类
    const categoriesContainer = $('.game-categories');
    categoriesContainer.empty();
    game.categories.forEach(category => {
        categoriesContainer.append(`
            <a href="/categories/${category.slug}/" class="badge bg-primary text-decoration-none me-1">${category.name}</a>
        `);
    });
    
    // 更新评论
    const commentsContainer = $('#comments .comments-list');
    commentsContainer.empty();
    
    if (data.comments.length === 0) {
        commentsContainer.append(`
            <div class="alert alert-light">
                暂无评论，快来抢沙发吧！
            </div>
        `);
    } else {
        data.comments.forEach(comment => {
            commentsContainer.append(createCommentHTML(comment));
        });
    }
    
    // 更新相关游戏
    const relatedGamesContainer = $('.related-games-container');
    relatedGamesContainer.empty();
    
    if (data.related_games.length === 0) {
        relatedGamesContainer.append(`
            <div class="col-12">
                <p class="text-center">暂无相关游戏</p>
            </div>
        `);
    } else {
        data.related_games.forEach(relatedGame => {
            relatedGamesContainer.append(createRelatedGameHTML(relatedGame));
        });
    }
    
    // 重新初始化交互
    initGameCardLinks();
}

/**
 * 创建评论HTML
 */
function createCommentHTML(comment) {
    const ratingStars = Array(5).fill().map((_, i) => 
        `<i class="fas fa-${i < comment.rating ? 'star' : 'star'} text-${i < comment.rating ? 'warning' : 'secondary'}"></i>`
    ).join('');
    
    const avatarUrl = comment.user.avatar_url || '/static/img/default-avatar.png';
    
    return `
        <div class="card mb-3">
            <div class="card-body">
                <div class="d-flex">
                    <div class="flex-shrink-0">
                        <div class="bg-light rounded-circle d-flex justify-content-center align-items-center comment-avatar">
                            <i class="fas fa-user fs-3"></i>
                        </div>
                    </div>
                    <div class="flex-grow-1 ms-3">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <h6 class="mb-0">${comment.user.username}</h6>
                            <small class="text-muted">${comment.created_at}</small>
                        </div>
                        <div class="mb-2">
                            ${ratingStars}
                        </div>
                        <p class="mb-0">${comment.content}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * 创建相关游戏HTML
 */
function createRelatedGameHTML(game) {
    const ratingStars = Array(5).fill().map((_, i) => {
        if (i < Math.floor(game.rating)) {
            return `<i class="fas fa-star"></i>`;
        } else if (i < game.rating) {
            return `<i class="fas fa-star-half-alt"></i>`;
        } else {
            return `<i class="far fa-star"></i>`;
        }
    }).join('');
    
    return `
        <div class="col-6">
            <div class="card h-100 border-0 game-card" data-game-id="${game.id}">
                <img src="${game.thumbnail_url}" class="card-img-top" alt="${game.title}">
                <div class="card-body px-0 pb-0">
                    <h6 class="card-title text-truncate">${game.title}</h6>
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="rating small">
                            ${ratingStars}
                        </div>
                        <small class="text-muted">${game.rating}</small>
                    </div>
                    <a href="/games/${game.slug}/" class="btn btn-sm btn-primary w-100 mt-2">开始游戏</a>
                </div>
            </div>
        </div>
    `;
}

/**
 * 更新评分显示
 */
function updateRatingDisplay(rating, commentCount) {
    const ratingContainer = $('.hero-section .rating');
    ratingContainer.empty();
    
    // 添加星星图标
    for (let i = 1; i <= 5; i++) {
        if (i <= Math.floor(rating)) {
            ratingContainer.append('<i class="fas fa-star"></i>');
        } else if (i <= rating + 0.5) {
            ratingContainer.append('<i class="fas fa-star-half-alt"></i>');
        } else {
            ratingContainer.append('<i class="far fa-star"></i>');
        }
    }
    
    // 更新评分文本
    ratingContainer.next('span').text(`${rating} (${commentCount})`);
}

/**
 * 初始化游戏卡片点击事件 - 使用AJAX加载游戏详情
 */
function initGameCardLinks() {
    const gameCards = document.querySelectorAll('.game-card a');
    
    gameCards.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // 检查链接是否包含game_detail路径
            if (href && href.includes('/games/')) {
                e.preventDefault();
                
                // 提取游戏ID
                const gameId = this.closest('.game-card').getAttribute('data-game-id');
                if (gameId) {
                    loadGameById(gameId, (err, result) => {
                        if (err || !result.success) {
                            // 如果AJAX加载失败，则回退到传统导航
                            window.location.href = href;
                        }
                    });
                } else {
                    // 如果找不到游戏ID，则回退到传统导航
                    window.location.href = href;
                }
            }
        });
    });
}

/**
 * 初始化游戏加载
 */
function initGameLoading() {
    const gameFrame = document.querySelector('.game-iframe');
    const loadingSpinner = document.querySelector('.game-loading');
    
    if (!gameFrame) return;
    
    // 如果有加载动画元素，显示加载动画
    if (loadingSpinner) {
    loadingSpinner.style.display = 'flex';
    }
    
    // 游戏加载完成后处理
    gameFrame.addEventListener('load', function() {
        // 隐藏加载动画（如果存在）
        if (loadingSpinner) {
        loadingSpinner.style.display = 'none';
        }
        
        // 显示游戏区域
        gameFrame.style.opacity = '1';
        
        // 记录游戏开始时间，用于统计游戏时长
        window.gameStartTime = new Date();
        
        // 记录游戏播放次数
        logGamePlay('start');
    });
    
    // 处理加载超时
    setTimeout(function() {
        if (loadingSpinner && loadingSpinner.style.display !== 'none') {
            // 显示超时提示
            const timeoutMessage = document.createElement('div');
            timeoutMessage.className = 'alert alert-warning text-center mt-3';
            timeoutMessage.innerHTML = '游戏加载时间较长，请耐心等待...<br><button class="btn btn-sm btn-primary mt-2 reload-game">重新加载</button>';
            
            if (loadingSpinner.parentNode) {
                loadingSpinner.parentNode.insertBefore(timeoutMessage, loadingSpinner.nextSibling);
            }
            
            // 添加重新加载按钮事件
            document.querySelector('.reload-game')?.addEventListener('click', function() {
                timeoutMessage.remove();
                reloadGameFrame(gameFrame);
            });
        }
    }, 10000); // 10秒后检查
}

/**
 * 重新加载游戏框架
 */
function reloadGameFrame(gameFrame) {
    if (!gameFrame) return;
    
    const src = gameFrame.src;
    gameFrame.src = '';
    
    setTimeout(() => {
        gameFrame.src = src;
    }, 100);
}

/**
 * 记录游戏行为
 */
function logGamePlay(action) {
    const gameId = document.querySelector('[data-game-id]')?.getAttribute('data-game-id');
    if (!gameId) return;
    
    // 准备请求数据
    const data = {
        action: action
    };
    
    if (action === 'end' && window.gameStartTime) {
        data.duration = Math.floor((new Date() - window.gameStartTime) / 1000);
    }
    
    // 使用apiRequest函数发送请求
    try {
        apiRequest({
            url: '/api/game/' + gameId + '/play/',
            method: 'POST',
            data: data,
            showMessage: false,
            onError: function(error) {
                console.error('游戏日志记录失败:', error);
            }
        });
    } catch(e) {
        console.error('游戏日志记录请求失败:', e);
    }
}

/**
 * 获取CSRF令牌
 */
function getCsrfToken() {
    // 首先尝试从表单字段获取
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenInput && tokenInput.value) {
        return tokenInput.value;
    }
    
    // 如果表单字段不存在，从cookie中获取
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');
    
    for (let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i].trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    
    return '';
}

/**
 * 初始化评论系统
 */
function initCommentSystem() {
    const commentForm = document.querySelector('form[action*="add_comment"]');
    const commentTabs = document.getElementById('comments-tab');
    const loadMoreBtn = document.getElementById('load-more-btn');
    
    // 检查评论表单是否已被模板脚本初始化，如果已初始化则跳过
    if (commentForm && commentForm.getAttribute('data-initialized') !== 'true') {
        // 提交评论表单前验证
        commentForm.addEventListener('submit', function(e) {
            const ratingInputs = this.querySelectorAll('input[name="rating"]');
            const contentInput = this.querySelector('textarea[name="content"]');
            let isRatingSelected = false;
            
            // 检查是否选择了评分
            ratingInputs.forEach(input => {
                if (input.checked) isRatingSelected = true;
            });
            
            if (!isRatingSelected) {
                e.preventDefault();
                showMessage('请选择评分星级', 'warning');
                return;
            }
            
            // 检查评论内容
            if (!contentInput.value.trim()) {
                e.preventDefault();
                showMessage('请输入评论内容', 'warning');
                return;
            }
        });
    }
    
    // 确保加载更多按钮不会重复绑定事件
    if (loadMoreBtn && loadMoreBtn.getAttribute('data-initialized') !== 'true') {
        // 让模板内的脚本处理，这里不做处理
        // 只需确保没有重复绑定
    }
    
    // 如果URL中有评论参数，切换到评论标签
    if (window.location.hash === '#comments' && commentTabs) {
        setTimeout(() => {
            commentTabs.click();
        }, 100);
    }
}

/**
 * 显示消息提示
 */
function showMessage(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // 5秒后自动关闭
    setTimeout(() => {
        if (alert.parentNode) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * 创建消息提示容器
 */
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}

/**
 * 初始化评分系统
 */
function initRatingSystem() {
    const ratingStars = document.querySelectorAll('.star-rating input');
    const ratingLabels = document.querySelectorAll('.star-rating label');
    
    if (!ratingStars.length) return;
    
    // 为每个星级评分输入框添加事件监听
    ratingStars.forEach(input => {
        input.addEventListener('change', function() {
            const value = this.value;
            
            // 更新星星显示
            ratingLabels.forEach(label => {
                label.classList.remove('active');
            });
            
            // 获取选中星星后的所有星星
            let current = this.nextElementSibling;
            while (current) {
                current.classList.add('active');
                current = current.nextElementSibling;
            }
        });
    });
}

/**
 * 初始化全屏按钮
 */
function initFullscreenButton() {
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    
    if (!fullscreenBtn) return;
    
    fullscreenBtn.addEventListener('click', function() {
        const gameContainer = document.querySelector('.game-iframe-container');
        
        if (!gameContainer) return;
        
        if (!document.fullscreenElement) {
            // 进入全屏模式
            if (gameContainer.requestFullscreen) {
                gameContainer.requestFullscreen().catch(err => {
                    console.error(`Error attempting to enable fullscreen: ${err.message}`);
                });
            } else if (gameContainer.mozRequestFullScreen) { /* Firefox */
                gameContainer.mozRequestFullScreen();
            } else if (gameContainer.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
                gameContainer.webkitRequestFullscreen();
            } else if (gameContainer.msRequestFullscreen) { /* IE/Edge */
                gameContainer.msRequestFullscreen();
            }
            
            fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i> 退出全屏';
        } else {
            // 退出全屏模式
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.mozCancelFullScreen) { /* Firefox */
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) { /* Chrome, Safari & Opera */
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) { /* IE/Edge */
                document.msExitFullscreen();
            }
            
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i> 全屏模式';
        }
    });
    
    // 监听全屏变化事件
    document.addEventListener('fullscreenchange', updateFullscreenButtonText);
    document.addEventListener('webkitfullscreenchange', updateFullscreenButtonText);
    document.addEventListener('mozfullscreenchange', updateFullscreenButtonText);
    document.addEventListener('MSFullscreenChange', updateFullscreenButtonText);
    
    function updateFullscreenButtonText() {
        if (document.fullscreenElement) {
            fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i> 退出全屏';
        } else {
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i> 全屏模式';
        }
    }
}

/**
 * 初始化收藏按钮
 */
function initFavoriteButton() {
    const favoriteBtn = document.querySelector('#favorite-btn');
    
    if (!favoriteBtn) return;
    
    // 检查按钮是否已经绑定了事件处理程序
    if (favoriteBtn.getAttribute('data-initialized') === 'true') {
        console.log('收藏按钮已经初始化，跳过');
        return;
    }
    
    // 标记按钮已初始化
    favoriteBtn.setAttribute('data-initialized', 'true');
    
    // 使用jQuery绑定的可能性较高，这里不再重复绑定事件
    // 让游戏详情页中的jQuery代码处理收藏功能
}

/**
 * 初始化分享按钮
 */
function initShareButton() {
    const shareBtn = document.getElementById('shareBtn');
    
    if (!shareBtn) return;
    
    shareBtn.addEventListener('click', function() {
        const gameTitle = document.querySelector('.hero-section h1')?.textContent || document.title;
        const gameDescription = document.querySelector('.hero-section p')?.textContent || '';
        
        if (navigator.share) {
            // 使用Web Share API (移动设备)
            navigator.share({
                title: gameTitle + ' - GameHub',
                text: gameDescription,
                url: window.location.href
            })
            .catch(err => {
                console.error('分享失败:', err);
                fallbackShare();
        });
    } else {
            // 后备方案：复制链接
            fallbackShare();
        }
        
        function fallbackShare() {
            // 创建一个临时输入框用于复制链接
            const tempInput = document.createElement('input');
            tempInput.value = window.location.href;
            document.body.appendChild(tempInput);
            tempInput.select();
            document.execCommand('copy');
            document.body.removeChild(tempInput);
            
            showMessage('链接已复制，可以分享给好友了', 'success');
        }
    });
}

/**
 * 初始化游戏卡片悬停效果
 */
function initGameCards() {
    const gameCards = document.querySelectorAll('.game-card');
    
    gameCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 5px 15px rgba(0,0,0,0.05)';
        });
    });
}

// 当页面关闭或用户离开时记录结束游戏
window.addEventListener('beforeunload', function() {
    if (window.gameStartTime) {
        logGamePlay('end');
    }
}); 

/**
 * 初始化浏览器导航事件处理
 * 处理浏览器的前进后退按钮
 */
function initBrowserNavigation() {
    // 监听popstate事件，处理浏览器前进后退按钮
    window.addEventListener('popstate', function(event) {
        const state = event.state;
        
        if (state && state.gameId) {
            // 如果有游戏ID，使用AJAX加载游戏详情
            loadGameById(state.gameId);
        } else {
            // 如果没有状态数据，则刷新页面
            window.location.reload();
        }
    });
    
    // 初始化当前页状态
    const currentGameId = document.querySelector('[data-game-id]')?.getAttribute('data-game-id');
    if (currentGameId) {
        // 替换当前历史记录状态
        window.history.replaceState({ gameId: currentGameId }, '', window.location.href);
    }
} 