/**
 * 移动端手势控制增强脚本
 * 提供游戏页面的高级手势控制功能
 * 支持多点触控、缩放和旋转手势
 */

document.addEventListener('DOMContentLoaded', function() {
    // 检测是否为移动设备
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // 初始化游戏页面手势控制
        initGameGestureControls();
    }
    
    /**
     * 初始化游戏页面的手势控制
     */
    function initGameGestureControls() {
        const gameIframe = document.querySelector('.game-iframe');
        const gameContainer = gameIframe ? gameIframe.parentElement : null;
        
        if (!gameContainer) return;
        
        // 添加游戏控制器UI（仅在游戏详情页面）
        if (document.querySelector('.game-details')) {
            addGameControlsUI(gameContainer);
        }
        
        // 处理方向滑动手势
        handleDirectionalSwipes(gameContainer);
        
        // 处理多点触控手势
        handleMultiTouchGestures(gameContainer);
    }
    
    /**
     * 添加游戏控制器UI
     * @param {HTMLElement} container - 游戏容器元素
     */
    function addGameControlsUI(container) {
        // 创建虚拟控制器容器
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'virtual-controls';
        controlsContainer.style.display = 'none'; // 默认隐藏，可通过按钮切换显示
        
        // 创建方向键
        const dpad = document.createElement('div');
        dpad.className = 'virtual-dpad';
        
        // 添加上下左右按钮
        ['up', 'right', 'down', 'left'].forEach(direction => {
            const btn = document.createElement('button');
            btn.className = `dpad-${direction}`;
            btn.setAttribute('data-direction', direction);
            btn.innerHTML = `<i class="fas fa-chevron-${direction}"></i>`;
            dpad.appendChild(btn);
            
            // 添加触摸事件
            btn.addEventListener('touchstart', function() {
                this.classList.add('active');
                simulateKeyEvent(direction, true);
            }, {passive: true});
            
            btn.addEventListener('touchend', function() {
                this.classList.remove('active');
                simulateKeyEvent(direction, false);
            }, {passive: true});
        });
        
        // 创建动作按钮
        const actionButtons = document.createElement('div');
        actionButtons.className = 'virtual-buttons';
        
        // 添加A和B按钮
        ['A', 'B'].forEach(button => {
            const btn = document.createElement('button');
            btn.className = `action-${button.toLowerCase()}`;
            btn.textContent = button;
            actionButtons.appendChild(btn);
            
            // 添加触摸事件
            btn.addEventListener('touchstart', function() {
                this.classList.add('active');
                simulateKeyEvent(button.toLowerCase(), true);
            }, {passive: true});
            
            btn.addEventListener('touchend', function() {
                this.classList.remove('active');
                simulateKeyEvent(button.toLowerCase(), false);
            }, {passive: true});
        });
        
        // 添加控制器切换按钮
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'controls-toggle btn btn-sm btn-secondary';
        toggleBtn.innerHTML = '<i class="fas fa-gamepad"></i>';
        toggleBtn.style.position = 'absolute';
        toggleBtn.style.left = '10px';
        toggleBtn.style.top = '10px';
        toggleBtn.style.zIndex = '100';
        toggleBtn.style.opacity = '0.7';
        
        toggleBtn.addEventListener('click', function() {
            if (controlsContainer.style.display === 'none') {
                controlsContainer.style.display = 'flex';
                this.classList.add('active');
            } else {
                controlsContainer.style.display = 'none';
                this.classList.remove('active');
            }
        });
        
        // 将所有元素添加到控制器容器
        controlsContainer.appendChild(dpad);
        controlsContainer.appendChild(actionButtons);
        
        // 将控制器和切换按钮添加到游戏容器
        container.appendChild(controlsContainer);
        container.appendChild(toggleBtn);
        
        // 添加控制器样式
        addControlsStyles();
    }
    
    /**
     * 处理方向滑动手势
     * @param {HTMLElement} element - 要添加手势的元素
     */
    function handleDirectionalSwipes(element) {
        let startX, startY, distX, distY;
        const threshold = 50; // 最小滑动距离
        
        // 触摸开始事件
        element.addEventListener('touchstart', function(e) {
            // 防止在虚拟控制器上触发
            if (e.target.closest('.virtual-controls')) return;
            
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }, {passive: true});
        
        // 触摸移动事件
        element.addEventListener('touchmove', function(e) {
            // 防止在虚拟控制器上触发
            if (e.target.closest('.virtual-controls') || !startX || !startY) return;
            
            distX = e.touches[0].clientX - startX;
            distY = e.touches[0].clientY - startY;
            
            // 判断是否达到滑动阈值
            if (Math.abs(distX) > threshold || Math.abs(distY) > threshold) {
                // 确定主要滑动方向
                if (Math.abs(distX) > Math.abs(distY)) {
                    // 水平滑动
                    simulateKeyEvent(distX > 0 ? 'right' : 'left', true);
                } else {
                    // 垂直滑动
                    simulateKeyEvent(distY > 0 ? 'down' : 'up', true);
                }
                
                // 重置起始位置以防止连续触发
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
            }
        }, {passive: true});
        
        // 触摸结束事件
        element.addEventListener('touchend', function(e) {
            // 防止在虚拟控制器上触发
            if (e.target.closest('.virtual-controls')) return;
            
            // 重置所有方向键
            ['up', 'right', 'down', 'left'].forEach(direction => {
                simulateKeyEvent(direction, false);
            });
            
            // 重置起始位置
            startX = null;
            startY = null;
        }, {passive: true});
    }
    
    /**
     * 处理多点触控手势（缩放、旋转等）
     * @param {HTMLElement} element - 要添加手势的元素
     */
    function handleMultiTouchGestures(element) {
        let initialDistance = 0;
        let currentScale = 1;
        const minScale = 0.5;
        const maxScale = 2;
        
        // 计算两个触摸点之间的距离
        function getDistance(touches) {
            const dx = touches[0].clientX - touches[1].clientX;
            const dy = touches[0].clientY - touches[1].clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }
        
        // 触摸开始事件
        element.addEventListener('touchstart', function(e) {
            // 防止在虚拟控制器上触发
            if (e.target.closest('.virtual-controls')) return;
            
            // 检测双指触摸（缩放手势）
            if (e.touches.length === 2) {
                initialDistance = getDistance(e.touches);
            }
        }, {passive: true});
        
        // 触摸移动事件
        element.addEventListener('touchmove', function(e) {
            // 防止在虚拟控制器上触发
            if (e.target.closest('.virtual-controls')) return;
            
            // 处理双指缩放
            if (e.touches.length === 2 && initialDistance > 0) {
                const currentDistance = getDistance(e.touches);
                const scale = currentDistance / initialDistance;
                
                // 计算新的缩放比例
                let newScale = currentScale * scale;
                newScale = Math.max(minScale, Math.min(maxScale, newScale));
                
                // 应用缩放到游戏iframe
                const gameIframe = element.querySelector('.game-iframe');
                if (gameIframe) {
                    gameIframe.style.transform = `scale(${newScale})`;
                    gameIframe.style.transformOrigin = 'center center';
                }
                
                // 更新初始距离和当前缩放比例
                initialDistance = currentDistance;
                currentScale = newScale;
                
                // 阻止默认行为（如页面缩放）
                e.preventDefault();
            }
        }, {passive: false});
        
        // 触摸结束事件
        element.addEventListener('touchend', function(e) {
            // 防止在虚拟控制器上触发
            if (e.target.closest('.virtual-controls')) return;
            
            // 重置初始距离
            if (e.touches.length < 2) {
                initialDistance = 0;
            }
        }, {passive: true});
    }
    
    /**
     * 模拟键盘事件
     * @param {string} key - 键名（up, down, left, right, a, b）
     * @param {boolean} isKeyDown - 是否是按下事件
     */
    function simulateKeyEvent(key, isKeyDown) {
        // 键名映射到键码
        const keyMap = {
            'up': 'ArrowUp',
            'down': 'ArrowDown',
            'left': 'ArrowLeft',
            'right': 'ArrowRight',
            'a': 'KeyA',
            'b': 'KeyB'
        };
        
        const keyCode = keyMap[key] || key;
        const eventType = isKeyDown ? 'keydown' : 'keyup';
        
        // 创建键盘事件
        const event = new KeyboardEvent(eventType, {
            key: keyCode,
            code: keyCode,
            bubbles: true,
            cancelable: true
        });
        
        // 向游戏iframe发送事件
        const gameIframe = document.querySelector('.game-iframe');
        if (gameIframe && gameIframe.contentWindow) {
            try {
                gameIframe.contentWindow.document.dispatchEvent(event);
            } catch (e) {
                // 如果因为跨域无法直接访问iframe内容，则向父文档发送事件
                document.dispatchEvent(event);
            }
        } else {
            // 如果没有找到iframe，则向当前文档发送事件
            document.dispatchEvent(event);
        }
    }
    
    /**
     * 添加虚拟控制器样式
     */
    function addControlsStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .virtual-controls {
                position: absolute;
                bottom: 20px;
                left: 0;
                right: 0;
                display: flex;
                justify-content: space-between;
                padding: 0 20px;
                z-index: 100;
            }
            
            .virtual-dpad {
                position: relative;
                width: 120px;
                height: 120px;
                background-color: rgba(0,0,0,0.2);
                border-radius: 60px;
            }
            
            .virtual-dpad button {
                position: absolute;
                width: 40px;
                height: 40px;
                background-color: rgba(255,255,255,0.7);
                border: none;
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #333;
            }
            
            .virtual-dpad button.active {
                background-color: rgba(0,123,255,0.7);
                color: white;
            }
            
            .dpad-up {
                top: 0;
                left: 50%;
                transform: translateX(-50%);
            }
            
            .dpad-right {
                right: 0;
                top: 50%;
                transform: translateY(-50%);
            }
            
            .dpad-down {
                bottom: 0;
                left: 50%;
                transform: translateX(-50%);
            }
            
            .dpad-left {
                left: 0;
                top: 50%;
                transform: translateY(-50%);
            }
            
            .virtual-buttons {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            
            .virtual-buttons button {
                width: 50px;
                height: 50px;
                background-color: rgba(255,255,255,0.7);
                border: none;
                border-radius: 25px;
                font-weight: bold;
                color: #333;
            }
            
            .virtual-buttons button.active {
                background-color: rgba(0,123,255,0.7);
                color: white;
            }
            
            .action-a {
                background-color: rgba(40,167,69,0.7) !important;
            }
            
            .action-b {
                background-color: rgba(220,53,69,0.7) !important;
            }
            
            .controls-toggle.active {
                background-color: #0d6efd !important;
                color: white;
                opacity: 1 !important;
            }
        `;
        document.head.appendChild(style);
    }
});