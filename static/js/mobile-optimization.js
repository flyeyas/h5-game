/**
 * 移动端优化脚本
 * 提供移动设备上的触控优化和性能增强
 * 支持多语言功能和SEO优化
 * 支持游戏全屏模式和手势控制
 */

document.addEventListener('DOMContentLoaded', function() {
    // 检测是否为移动设备
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // 为移动设备添加特定类
        document.body.classList.add('mobile-device');
        
        // 优化触控事件
        optimizeTouchEvents();
        
        // 延迟加载非关键资源
        deferNonCriticalResources();
        
        // 优化语言切换器在移动设备上的体验
        optimizeLanguageSwitcher();
        
        // 添加全屏模式支持
        enableFullscreenMode();
        
        // 添加手势控制支持
        enableGestureControls();
    }
    
    /**
     * 优化触控事件，提高移动设备上的响应速度
     */
    function optimizeTouchEvents() {
        // 移除点击延迟
        const touchElements = document.querySelectorAll('.game-card, .btn, a, .dropdown-item');
        touchElements.forEach(element => {
            element.addEventListener('touchstart', function() {}, {passive: true});
        });
        
        // 为游戏卡片添加触控反馈
        const gameCards = document.querySelectorAll('.game-card');
        gameCards.forEach(card => {
            card.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            }, {passive: true});
            
            card.addEventListener('touchend', function() {
                this.classList.remove('touch-active');
            }, {passive: true});
        });
    }
    
    /**
     * 延迟加载非关键资源以提高页面加载速度
     */
    function deferNonCriticalResources() {
        // 延迟加载图片
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            lazyImages.forEach(img => {
                imageObserver.observe(img);
            });
        } else {
            // 回退方案：简单的延迟加载
            setTimeout(() => {
                lazyImages.forEach(img => {
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                });
            }, 1000);
        }
    }
    
    /**
     * 优化语言切换器在移动设备上的体验
     */
    function optimizeLanguageSwitcher() {
        // 增强语言切换按钮的可点击区域
        const languageDropdown = document.getElementById('languageDropdown');
        if (languageDropdown) {
            languageDropdown.style.padding = '0.75rem 1rem';
        }
        
        // 优化语言切换表单的提交
        const languageForms = document.querySelectorAll('.language-form');
        languageForms.forEach(form => {
            const button = form.querySelector('button');
            if (button) {
                // 增加按钮的可点击区域
                button.style.padding = '0.75rem 1.5rem';
                
                // 添加触摸反馈
                button.addEventListener('touchstart', function() {
                    this.classList.add('touch-active');
                }, {passive: true});
                
                button.addEventListener('touchend', function() {
                    this.classList.remove('touch-active');
                    // 短暂延迟以显示视觉反馈
                    setTimeout(() => {
                        form.submit();
                    }, 150);
                }, {passive: true});
            }
        });
    }
    
    /**
     * 启用游戏全屏模式功能
     */
    function enableFullscreenMode() {
        // 查找游戏iframe
        const gameIframe = document.querySelector('.game-iframe');
        if (!gameIframe) return;
        
        // 创建全屏按钮
        const fullscreenBtn = document.createElement('button');
        fullscreenBtn.className = 'btn btn-sm btn-light fullscreen-btn';
        fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        fullscreenBtn.setAttribute('aria-label', 'Fullscreen');
        
        // 将全屏按钮添加到游戏容器
        const gameContainer = gameIframe.parentElement;
        if (gameContainer) {
            gameContainer.style.position = 'relative';
            fullscreenBtn.style.position = 'absolute';
            fullscreenBtn.style.right = '10px';
            fullscreenBtn.style.top = '10px';
            fullscreenBtn.style.zIndex = '100';
            fullscreenBtn.style.opacity = '0.7';
            gameContainer.appendChild(fullscreenBtn);
            
            // 添加全屏切换事件
            fullscreenBtn.addEventListener('click', function() {
                toggleFullscreen(gameContainer);
            });
        }
    }
    
    /**
     * 切换全屏模式
     * @param {HTMLElement} element - 要全屏显示的元素
     */
    function toggleFullscreen(element) {
        if (!document.fullscreenElement &&
            !document.mozFullScreenElement &&
            !document.webkitFullscreenElement &&
            !document.msFullscreenElement) {
            // 进入全屏模式
            if (element.requestFullscreen) {
                element.requestFullscreen();
            } else if (element.msRequestFullscreen) {
                element.msRequestFullscreen();
            } else if (element.mozRequestFullScreen) {
                element.mozRequestFullScreen();
            } else if (element.webkitRequestFullscreen) {
                element.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
            }
        } else {
            // 退出全屏模式
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            }
        }
    }
    
    /**
     * 启用移动端手势控制
     */
    function enableGestureControls() {
        // 查找游戏列表和详情页面的可滑动元素
        const swipeElements = document.querySelectorAll('.game-list, .game-details');
        
        swipeElements.forEach(element => {
            let startX, startY, distX, distY;
            const threshold = 100; // 最小滑动距离
            
            // 触摸开始事件
            element.addEventListener('touchstart', function(e) {
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
            }, {passive: true});
            
            // 触摸结束事件
            element.addEventListener('touchend', function(e) {
                if (!startX || !startY) return;
                
                distX = e.changedTouches[0].clientX - startX;
                distY = e.changedTouches[0].clientY - startY;
                
                // 判断是水平滑动还是垂直滑动
                if (Math.abs(distX) > Math.abs(distY)) {
                    // 水平滑动
                    if (Math.abs(distX) > threshold) {
                        if (distX > 0) {
                            // 向右滑动 - 上一页或上一个项目
                            const prevBtn = document.querySelector('.pagination .page-item:not(.disabled) .page-link[aria-label="Previous"]');
                            if (prevBtn) prevBtn.click();
                        } else {
                            // 向左滑动 - 下一页或下一个项目
                            const nextBtn = document.querySelector('.pagination .page-item:not(.disabled) .page-link[aria-label="Next"]');
                            if (nextBtn) nextBtn.click();
                        }
                    }
                }
                
                // 重置起始位置
                startX = null;
                startY = null;
            }, {passive: true});
        });
    }
    
    /**
     * 优化图片加载策略
     * 增强了原有的延迟加载功能
     */
    function deferNonCriticalResources() {
        // 延迟加载图片
        const lazyImages = document.querySelectorAll('img[loading="lazy"], img.lazy, .lazy-bg');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        
                        if (element.tagName.toLowerCase() === 'img') {
                            // 处理图片元素
                            if (element.dataset.src) {
                                element.src = element.dataset.src;
                                element.removeAttribute('data-src');
                            }
                            if (element.dataset.srcset) {
                                element.srcset = element.dataset.srcset;
                                element.removeAttribute('data-srcset');
                            }
                        } else {
                            // 处理背景图片元素
                            if (element.dataset.bg) {
                                element.style.backgroundImage = `url(${element.dataset.bg})`;
                                element.removeAttribute('data-bg');
                            }
                        }
                        
                        element.classList.remove('lazy', 'lazy-bg');
                        imageObserver.unobserve(element);
                    }
                });
            }, {
                rootMargin: '200px 0px', // 提前200px开始加载
                threshold: 0.01 // 只需要很小一部分进入视口就开始加载
            });
            
            lazyImages.forEach(element => {
                imageObserver.observe(element);
            });
        } else {
            // 回退方案：简单的延迟加载
            setTimeout(() => {
                lazyImages.forEach(element => {
                    if (element.tagName.toLowerCase() === 'img') {
                        if (element.dataset.src) {
                            element.src = element.dataset.src;
                        }
                        if (element.dataset.srcset) {
                            element.srcset = element.dataset.srcset;
                        }
                    } else {
                        if (element.dataset.bg) {
                            element.style.backgroundImage = `url(${element.dataset.bg})`;
                        }
                    }
                    element.classList.remove('lazy', 'lazy-bg');
                });
            }, 1000);
        }
        
        // 延迟加载非关键JavaScript
        const lazyScripts = document.querySelectorAll('script[data-src]');
        setTimeout(() => {
            lazyScripts.forEach(script => {
                script.src = script.dataset.src;
                script.removeAttribute('data-src');
            });
        }, 2000);
    }
    
    // 添加移动端特定样式
    if (isMobile) {
        const style = document.createElement('style');
        style.textContent = `
            .touch-active {
                transform: scale(0.98) !important;
                transition: transform 0.1s ease !important;
            }
            .game-card {
                -webkit-tap-highlight-color: transparent;
            }
            .btn {
                padding: 0.5rem 1rem;
                font-size: 1rem;
            }
            .dropdown-item {
                padding: 0.75rem 1.5rem;
            }
            .language-menu .dropdown-item {
                font-size: 1.1rem;
                display: flex;
                align-items: center;
            }
            .language-menu .dropdown-item.active {
                background-color: rgba(0,123,255,0.1);
                color: #0d6efd;
                font-weight: 500;
            }
            .fullscreen-btn {
                opacity: 0.7;
                transition: opacity 0.3s ease;
            }
            .fullscreen-btn:hover, .fullscreen-btn:focus {
                opacity: 1;
            }
            .game-iframe-container {
                position: relative;
            }
            @media (max-width: 768px) {
                .game-card .card-title {
                    font-size: 1rem;
                }
                .game-card .card-text {
                    font-size: 0.85rem;
                }
                .btn-sm {
                    padding: 0.25rem 0.5rem;
                    font-size: 0.875rem;
                }
            }
        `;
        document.head.appendChild(style);
    }
});