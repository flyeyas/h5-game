/**
 * 游戏全屏模式增强脚本
 * 提供更好的游戏全屏体验和屏幕方向控制
 * 支持移动设备的屏幕旋转锁定和全屏通知
 */

document.addEventListener('DOMContentLoaded', function() {
    // 检测是否为移动设备
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // 初始化全屏增强功能
        initFullscreenEnhancements();
    }
    
    /**
     * 初始化全屏增强功能
     */
    function initFullscreenEnhancements() {
        const gameIframe = document.querySelector('.game-iframe');
        const gameContainer = gameIframe ? gameIframe.parentElement : null;
        
        if (!gameContainer) return;
        
        // 添加全屏增强功能
        enhanceFullscreenExperience(gameContainer);
        
        // 添加屏幕方向控制
        addOrientationControl(gameContainer);
        
        // 监听全屏变化事件
        monitorFullscreenChanges(gameContainer);
    }
    
    /**
     * 增强全屏体验
     * @param {HTMLElement} container - 游戏容器元素
     */
    function enhanceFullscreenExperience(container) {
        // 创建全屏提示覆盖层
        const overlay = document.createElement('div');
        overlay.className = 'fullscreen-overlay';
        overlay.innerHTML = `
            <div class="overlay-content">
                <i class="fas fa-expand fa-2x"></i>
                <p>点击进入全屏模式获得最佳游戏体验</p>
            </div>
        `;
        overlay.style.display = 'none';
        
        // 将覆盖层添加到游戏容器
        container.appendChild(overlay);
        
        // 为新用户显示全屏提示（仅显示一次）
        if (!localStorage.getItem('fullscreen_tip_shown')) {
            setTimeout(() => {
                overlay.style.display = 'flex';
                
                // 3秒后自动隐藏
                setTimeout(() => {
                    overlay.style.display = 'none';
                    localStorage.setItem('fullscreen_tip_shown', 'true');
                }, 3000);
            }, 2000);
        }
        
        // 点击覆盖层进入全屏
        overlay.addEventListener('click', function() {
            toggleFullscreen(container);
            this.style.display = 'none';
        });
        
        // 添加全屏样式
        addFullscreenStyles();
    }
    
    /**
     * 添加屏幕方向控制
     * @param {HTMLElement} container - 游戏容器元素
     */
    function addOrientationControl(container) {
        // 创建屏幕方向切换按钮
        const orientationBtn = document.createElement('button');
        orientationBtn.className = 'orientation-toggle btn btn-sm btn-light';
        orientationBtn.innerHTML = '<i class="fas fa-mobile-alt"></i>';
        orientationBtn.setAttribute('aria-label', 'Toggle Orientation');
        orientationBtn.style.position = 'absolute';
        orientationBtn.style.right = '60px'; // 放在全屏按钮旁边
        orientationBtn.style.top = '10px';
        orientationBtn.style.zIndex = '100';
        orientationBtn.style.opacity = '0.7';
        
        // 将按钮添加到游戏容器
        container.appendChild(orientationBtn);
        
        // 当前方向状态
        let isLandscape = false;
        
        // 点击切换屏幕方向
        orientationBtn.addEventListener('click', function() {
            isLandscape = !isLandscape;
            
            // 更新按钮图标
            this.innerHTML = isLandscape ? 
                '<i class="fas fa-mobile-alt fa-rotate-90"></i>' : 
                '<i class="fas fa-mobile-alt"></i>';
            
            // 尝试锁定屏幕方向
            lockScreenOrientation(isLandscape ? 'landscape' : 'portrait');
        });
    }
    
    /**
     * 尝试锁定屏幕方向
     * @param {string} orientation - 要锁定的方向 ('landscape' 或 'portrait')
     */
    function lockScreenOrientation(orientation) {
        try {
            // 尝试使用Screen Orientation API
            if (screen.orientation && screen.orientation.lock) {
                screen.orientation.lock(orientation === 'landscape' ? 'landscape' : 'portrait')
                    .catch(e => console.warn('无法锁定屏幕方向:', e));
            } 
            // 回退到较旧的方法
            else if (screen.lockOrientation) {
                screen.lockOrientation(orientation === 'landscape' ? 'landscape' : 'portrait');
            } else if (screen.mozLockOrientation) {
                screen.mozLockOrientation(orientation === 'landscape' ? 'landscape' : 'portrait');
            } else if (screen.msLockOrientation) {
                screen.msLockOrientation(orientation === 'landscape' ? 'landscape' : 'portrait');
            } else {
                // 如果API不可用，显示提示
                showOrientationToast(orientation);
            }
        } catch (e) {
            console.warn('锁定屏幕方向时出错:', e);
            // 显示手动旋转提示
            showOrientationToast(orientation);
        }
    }
    
    /**
     * 显示屏幕方向提示
     * @param {string} orientation - 建议的方向
     */
    function showOrientationToast(orientation) {
        // 创建提示元素
        const toast = document.createElement('div');
        toast.className = 'orientation-toast';
        toast.innerHTML = `
            <i class="fas fa-${orientation === 'landscape' ? 'mobile-alt fa-rotate-90' : 'mobile-alt'}"></i>
            <p>请${orientation === 'landscape' ? '横向' : '竖向'}持握设备以获得最佳体验</p>
        `;
        
        // 添加到文档
        document.body.appendChild(toast);
        
        // 2秒后自动移除
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 500);
        }, 2000);
    }
    
    /**
     * 监听全屏变化事件
     * @param {HTMLElement} container - 游戏容器元素
     */
    function monitorFullscreenChanges(container) {
        // 监听全屏变化事件
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('mozfullscreenchange', handleFullscreenChange);
        document.addEventListener('MSFullscreenChange', handleFullscreenChange);
        
        function handleFullscreenChange() {
            const isFullscreen = !!document.fullscreenElement || 
                                !!document.webkitFullscreenElement || 
                                !!document.mozFullScreenElement || 
                                !!document.msFullscreenElement;
            
            // 更新全屏按钮图标
            const fullscreenBtn = container.querySelector('.fullscreen-btn');
            if (fullscreenBtn) {
                fullscreenBtn.innerHTML = isFullscreen ? 
                    '<i class="fas fa-compress"></i>' : 
                    '<i class="fas fa-expand"></i>';
            }
            
            // 在全屏模式下自动尝试横屏
            if (isFullscreen) {
                lockScreenOrientation('landscape');
                
                // 在全屏模式下添加退出提示
                showExitFullscreenTip();
            }
        }
    }
    
    /**
     * 显示退出全屏提示
     */
    function showExitFullscreenTip() {
        // 创建提示元素
        const tip = document.createElement('div');
        tip.className = 'exit-fullscreen-tip';
        tip.innerHTML = '<p>按 ESC 键或再次点击全屏按钮退出全屏</p>';
        
        // 添加到文档
        document.body.appendChild(tip);
        
        // 2秒后自动移除
        setTimeout(() => {
            tip.classList.add('fade-out');
            setTimeout(() => {
                if (document.body.contains(tip)) {
                    document.body.removeChild(tip);
                }
            }, 500);
        }, 2000);
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
     * 添加全屏相关样式
     */
    function addFullscreenStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .fullscreen-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0,0,0,0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                cursor: pointer;
            }
            
            .overlay-content {
                text-align: center;
                color: white;
                padding: 20px;
                background-color: rgba(0,0,0,0.5);
                border-radius: 10px;
            }
            
            .overlay-content i {
                margin-bottom: 10px;
            }
            
            .orientation-toast {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background-color: rgba(0,0,0,0.8);
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                display: flex;
                align-items: center;
                gap: 10px;
                z-index: 10000;
                animation: fade-in 0.3s ease;
            }
            
            .exit-fullscreen-tip {
                position: fixed;
                top: 10px;
                left: 50%;
                transform: translateX(-50%);
                background-color: rgba(0,0,0,0.8);
                color: white;
                padding: 5px 15px;
                border-radius: 5px;
                font-size: 0.9rem;
                z-index: 10000;
                animation: fade-in 0.3s ease;
            }
            
            .fade-out {
                animation: fade-out 0.5s ease forwards;
            }
            
            @keyframes fade-in {
                from { opacity: 0; transform: translate(-50%, 20px); }
                to { opacity: 1; transform: translate(-50%, 0); }
            }
            
            @keyframes fade-out {
                from { opacity: 1; transform: translate(-50%, 0); }
                to { opacity: 0; transform: translate(-50%, 20px); }
            }
            
            /* 全屏模式下的样式 */
            :fullscreen .game-iframe-container {
                width: 100vw;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: black;
            }
            
            :fullscreen .game-iframe {
                max-width: 100%;
                max-height: 100%;
                margin: auto;
            }
            
            /* 兼容不同浏览器的全屏样式 */
            :-webkit-full-screen .game-iframe-container {
                width: 100vw;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: black;
            }
            
            :-moz-full-screen .game-iframe-container {
                width: 100vw;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: black;
            }
            
            :-ms-fullscreen .game-iframe-container {
                width: 100vw;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: black;
            }
        `;
        document.head.appendChild(style);
    }
});