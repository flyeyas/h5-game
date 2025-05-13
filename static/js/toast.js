/**
 * 全局Toast提示组件
 * 用于在异步请求后向用户展示反馈信息
 */

// Toast类型定义
const TOAST_TYPES = {
    SUCCESS: 'success',
    ERROR: 'error',
    INFO: 'info',
    WARNING: 'warning'
};

// Toast默认配置
const TOAST_DEFAULTS = {
    duration: 3000,        // 显示时长(毫秒)
    position: 'bottom-right', // 位置：'top-right', 'top-center', 'top-left', 'bottom-right', 'bottom-center', 'bottom-left'
    maxToasts: 5,          // 最大同时显示数量
    showProgress: true,    // 是否显示进度条
    pauseOnHover: true,    // 鼠标悬停时暂停倒计时
    closeButton: true,     // 是否显示关闭按钮
    darkMode: false        // 暗黑模式
};

// 当前配置
let toastConfig = { ...TOAST_DEFAULTS };

// 记录活动的toast列表
let activeToasts = [];

/**
 * 创建并显示一个Toast提示
 * @param {string} message - 要显示的消息
 * @param {string} type - 提示类型：'success', 'error', 'info', 'warning'
 * @param {Object} options - 可选配置参数
 * @returns {Object} - 返回Toast实例，可用于手动关闭
 */
function showToast(message, type = TOAST_TYPES.SUCCESS, options = {}) {
    // 合并选项
    const config = { ...toastConfig, ...options };
    type = Object.values(TOAST_TYPES).includes(type) ? type : TOAST_TYPES.INFO;
    
    // 确保容器存在
    const container = ensureContainer(config.position);
    
    // 限制最大数量
    limitToastCount(config.maxToasts);
    
    // 创建Toast元素
    const toast = createToastElement(message, type, config);
    container.appendChild(toast);
    
    // 添加到活动列表
    const toastObj = {
        id: Date.now().toString(),
        element: toast,
        timeoutId: null,
        isPaused: false,
        remainingTime: config.duration,
        startTime: Date.now()
    };
    
    activeToasts.push(toastObj);
    
    // 设置自动消失
    if (config.duration > 0) {
        toastObj.timeoutId = setTimeout(() => {
            removeToast(toastObj);
        }, config.duration);
        
        // 添加进度条
        if (config.showProgress) {
            const progressBar = toast.querySelector('.toast-progress');
            if (progressBar) {
                progressBar.style.transition = `width ${config.duration / 1000}s linear`;
                // 触发重绘
                progressBar.offsetHeight;
                progressBar.style.width = '0%';
            }
        }
    }
    
    // 鼠标悬停暂停
    if (config.pauseOnHover) {
        toast.addEventListener('mouseenter', () => {
            if (toastObj.timeoutId) {
                clearTimeout(toastObj.timeoutId);
                toastObj.timeoutId = null;
                toastObj.isPaused = true;
                toastObj.remainingTime = toastObj.remainingTime - (Date.now() - toastObj.startTime);
                
                // 暂停进度条动画
                const progressBar = toast.querySelector('.toast-progress');
                if (progressBar) {
                    progressBar.style.animationPlayState = 'paused';
                    progressBar.style.transition = 'none';
                }
            }
        });
        
        toast.addEventListener('mouseleave', () => {
            if (toastObj.isPaused) {
                toastObj.isPaused = false;
                toastObj.startTime = Date.now();
                
                // 继续倒计时
                toastObj.timeoutId = setTimeout(() => {
                    removeToast(toastObj);
                }, toastObj.remainingTime);
                
                // 继续进度条动画
                const progressBar = toast.querySelector('.toast-progress');
                if (progressBar && config.showProgress) {
                    progressBar.style.transition = `width ${toastObj.remainingTime / 1000}s linear`;
                    // 触发重绘
                    progressBar.offsetHeight;
                    progressBar.style.width = '0%';
                }
            }
        });
    }
    
    // 显示Toast
    setTimeout(() => {
        toast.classList.add('toast-visible');
    }, 10);
    
    // 返回Toast实例
    return {
        close: () => removeToast(toastObj),
        id: toastObj.id
    };
}

/**
 * 确保Toast容器存在
 * @param {string} position - Toast显示位置
 * @returns {HTMLElement} - Toast容器元素
 */
function ensureContainer(position) {
    let containerId = `toast-container-${position}`;
    let container = document.getElementById(containerId);
    
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = `toast-container toast-${position}`;
        document.body.appendChild(container);
        
        // 添加样式
        let style = document.getElementById('toast-style');
        if (!style) {
            style = document.createElement('style');
            style.id = 'toast-style';
            style.textContent = getToastStyles();
            document.head.appendChild(style);
        }
    }
    
    return container;
}

/**
 * 限制Toast数量
 * @param {number} maxCount - 最大允许的Toast数量
 */
function limitToastCount(maxCount) {
    while (activeToasts.length >= maxCount) {
        const oldestToast = activeToasts[0];
        removeToast(oldestToast);
    }
}

/**
 * 创建Toast元素
 * @param {string} message - 要显示的消息
 * @param {string} type - Toast类型
 * @param {Object} config - 配置选项
 * @returns {HTMLElement} - 创建的Toast元素
 */
function createToastElement(message, type, config) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} ${config.darkMode ? 'toast-dark' : ''}`;
    toast.setAttribute('role', 'alert');
    
    // 设置图标
    let icon = '';
    switch (type) {
        case TOAST_TYPES.SUCCESS:
            icon = '<i class="fas fa-check-circle"></i>';
            break;
        case TOAST_TYPES.ERROR:
            icon = '<i class="fas fa-times-circle"></i>';
            break;
        case TOAST_TYPES.WARNING:
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            break;
        case TOAST_TYPES.INFO:
            icon = '<i class="fas fa-info-circle"></i>';
            break;
    }
    
    // 构建内容
    toast.innerHTML = `
        <div class="toast-content">
            ${icon ? `<div class="toast-icon">${icon}</div>` : ''}
            <div class="toast-message">${message}</div>
            ${config.closeButton ? '<button class="toast-close">&times;</button>' : ''}
        </div>
        ${config.showProgress ? '<div class="toast-progress"></div>' : ''}
    `;
    
    // 添加关闭按钮事件
    if (config.closeButton) {
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                const toastObj = activeToasts.find(t => t.element === toast);
                if (toastObj) {
                    removeToast(toastObj);
                }
            });
        }
    }
    
    return toast;
}

/**
 * 移除Toast
 * @param {Object} toastObj - Toast对象
 */
function removeToast(toastObj) {
    if (!toastObj || !toastObj.element) return;
    
    // 清除计时器
    if (toastObj.timeoutId) {
        clearTimeout(toastObj.timeoutId);
        toastObj.timeoutId = null;
    }
    
    // 标记为正在移除
    toastObj.element.classList.add('toast-hiding');
    
    // 移除DOM元素
    setTimeout(() => {
        if (toastObj.element && toastObj.element.parentNode) {
            toastObj.element.parentNode.removeChild(toastObj.element);
        }
        
        // 从活动列表中移除
        const index = activeToasts.findIndex(t => t.id === toastObj.id);
        if (index !== -1) {
            activeToasts.splice(index, 1);
        }
        
        // 检查容器是否为空，如果为空则移除容器
        const containers = document.querySelectorAll('.toast-container');
        containers.forEach(container => {
            if (!container.hasChildNodes()) {
                container.parentNode.removeChild(container);
            }
        });
    }, 300); // 等待淡出动画完成
}

/**
 * 关闭所有Toast
 */
function closeAllToasts() {
    [...activeToasts].forEach(removeToast);
}

/**
 * 更新Toast配置
 * @param {Object} newConfig - 新的配置
 */
function configureToast(newConfig) {
    toastConfig = { ...toastConfig, ...newConfig };
}

/**
 * 获取Toast样式
 * @returns {string} - CSS样式字符串
 */
function getToastStyles() {
    return `
        .toast-container {
            position: fixed;
            z-index: 9999;
            padding: 15px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            max-width: 100%;
            max-height: 100vh;
            overflow-y: auto;
            pointer-events: none;
        }
        
        .toast-top-right {
            top: 0;
            right: 0;
            align-items: flex-end;
        }
        
        .toast-top-center {
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            align-items: center;
        }
        
        .toast-top-left {
            top: 0;
            left: 0;
            align-items: flex-start;
        }
        
        .toast-bottom-right {
            bottom: 0;
            right: 0;
            align-items: flex-end;
        }
        
        .toast-bottom-center {
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            align-items: center;
        }
        
        .toast-bottom-left {
            bottom: 0;
            left: 0;
            align-items: flex-start;
        }
        
        .toast {
            position: relative;
            margin-bottom: 10px;
            padding: 10px 15px;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            min-width: 250px;
            max-width: 450px;
            background-color: #fff;
            color: #333;
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.3s, transform 0.3s;
            pointer-events: auto;
            overflow: hidden;
        }
        
        .toast-visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        .toast-hiding {
            opacity: 0;
            transform: translateY(-20px);
        }
        
        .toast-content {
            display: flex;
            align-items: center;
        }
        
        .toast-icon {
            margin-right: 12px;
            font-size: 20px;
        }
        
        .toast-message {
            flex: 1;
            font-size: 14px;
            line-height: 1.4;
            word-break: break-word;
        }
        
        .toast-close {
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            margin-left: 10px;
            padding: 0;
            color: inherit;
            opacity: 0.7;
            transition: opacity 0.3s;
            line-height: 1;
        }
        
        .toast-close:hover {
            opacity: 1;
        }
        
        .toast-progress {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 3px;
        }
        
        .toast-success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border-left: 4px solid #4caf50;
        }
        
        .toast-success .toast-progress {
            background-color: #4caf50;
        }
        
        .toast-error {
            background-color: #ffebee;
            color: #c62828;
            border-left: 4px solid #f44336;
        }
        
        .toast-error .toast-progress {
            background-color: #f44336;
        }
        
        .toast-warning {
            background-color: #fff8e1;
            color: #ff8f00;
            border-left: 4px solid #ffc107;
        }
        
        .toast-warning .toast-progress {
            background-color: #ffc107;
        }
        
        .toast-info {
            background-color: #e3f2fd;
            color: #0d47a1;
            border-left: 4px solid #2196f3;
        }
        
        .toast-info .toast-progress {
            background-color: #2196f3;
        }
        
        .toast-dark {
            background-color: #333;
            color: #fff;
        }
        
        /* 暗黑主题变体 */
        .toast-dark.toast-success {
            background-color: #2e7d32;
            color: #fff;
            border-left: 4px solid #81c784;
        }
        
        .toast-dark.toast-error {
            background-color: #c62828;
            color: #fff;
            border-left: 4px solid #e57373;
        }
        
        .toast-dark.toast-warning {
            background-color: #ff8f00;
            color: #fff;
            border-left: 4px solid #ffd54f;
        }
        
        .toast-dark.toast-info {
            background-color: #0d47a1;
            color: #fff;
            border-left: 4px solid #64b5f6;
        }
        
        /* 响应式调整 */
        @media (max-width: 480px) {
            .toast-container {
                padding: 10px;
                width: 100%;
            }
            
            .toast {
                min-width: 0;
                max-width: 100%;
                width: 100%;
            }
        }
    `;
}

// 便捷方法
const toast = {
    success: (message, options) => showToast(message, TOAST_TYPES.SUCCESS, options),
    error: (message, options) => showToast(message, TOAST_TYPES.ERROR, options),
    info: (message, options) => showToast(message, TOAST_TYPES.INFO, options),
    warning: (message, options) => showToast(message, TOAST_TYPES.WARNING, options),
    closeAll: closeAllToasts,
    configure: configureToast
};

// 暴露API
window.toast = toast;
window.showToast = showToast; 