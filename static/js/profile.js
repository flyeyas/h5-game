/**
 * 用户个人资料页面JavaScript功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化用户信息编辑功能
    initProfileEdit();
    
    // 初始化用户收藏游戏功能
    initFavoriteGames();
    
    // 初始化游戏历史记录功能
    initGameHistory();
    
    // 初始化消息通知功能
    initNotifications();
    
    // 初始化用户设置功能
    initUserSettings();
    
    // 初始化标签页切换
    initTabSwitching();
});

/**
 * 初始化用户个人资料编辑功能
 */
function initProfileEdit() {
    const profileForm = document.getElementById('profileForm');
    const saveProfileBtn = document.getElementById('saveProfileBtn');
    
    if (!profileForm) return;
    
    // 保存个人资料
    if (saveProfileBtn && profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 获取表单数据
            const formData = new FormData(profileForm);
            
            // 显示加载状态
            saveProfileBtn.disabled = true;
            saveProfileBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 保存中...';
            
            // 使用apiRequest函数发送请求
            apiRequest({
                url: '/profile/update/',
                method: 'POST',
                data: formData,
                useFormData: true,
                success: function(response) {
                    // 更新显示的用户信息
                    const username = formData.get('username');
                    const bio = formData.get('bio');
                    
                    if (username) {
                        document.querySelectorAll('.profile-username').forEach(el => {
                            el.textContent = username;
                        });
                    }
                    
                    if (bio) {
                        document.querySelector('.profile-bio')?.textContent = bio;
                    }
                    
                    // 更新头像预览
                    const randomAvatarUrl = formData.get('random_avatar_url');
                    if (randomAvatarUrl) {
                        document.querySelectorAll('.profile-avatar').forEach(el => {
                            el.src = randomAvatarUrl;
                        });
                    }
                    
                    // 显示成功消息
                    showToast('success', response.message || '个人资料已成功更新！');
                    
                    // 恢复按钮状态
                    saveProfileBtn.disabled = false;
                    saveProfileBtn.textContent = '保存更改';
                },
                error: function(response) {
                    // 恢复按钮状态
                    saveProfileBtn.disabled = false;
                    saveProfileBtn.textContent = '保存更改';
                    
                    // 显示错误信息通过 Bootstrap Toast
                    showToast('error', response.message || '保存失败，请稍后再试');
                },
                onComplete: function() {
                    // 操作完成时执行，无论成功或失败
                    saveProfileBtn.disabled = false;
                    saveProfileBtn.textContent = '保存更改';
                }
            });
        });
    }
}

// Bootstrap Toast 显示函数
function showToast(type, message) {
    // 创建 toast 元素
    const toastEl = document.createElement('div');
    toastEl.className = 'toast';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // 根据类型设置背景颜色
    if (type === 'success') {
        toastEl.classList.add('bg-success', 'text-white');
    } else if (type === 'error' || type === 'danger') {
        toastEl.classList.add('bg-danger', 'text-white');
    } else if (type === 'warning') {
        toastEl.classList.add('bg-warning', 'text-dark');
    } else if (type === 'info') {
        toastEl.classList.add('bg-info', 'text-dark');
    }
    
    // 创建 toast 内容
    toastEl.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">提示</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // 添加到 toast 容器
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    toastContainer.appendChild(toastEl);
    
    // 初始化 Bootstrap Toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 3000
    });
    
    // 显示 Toast
    toast.show();
    
    // Toast 隐藏后移除元素
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// 创建 Toast 容器
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

/**
 * 显示提示消息
 */
function showMessage(message, type = 'info') {
    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // 3秒后自动关闭
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
        }, 150);
    }, 3000);
}

/**
 * 创建提示消息容器
 */
function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container';
    document.body.appendChild(container);
    return container;
}

/**
 * 初始化收藏游戏功能
 */
function initFavoriteGames() {
    const favoritesList = document.querySelector('.favorites-list');
    const emptyFavorites = document.querySelector('.empty-favorites');
    
    if (!favoritesList) return;
    
    // 删除收藏游戏
    favoritesList.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-favorite') || e.target.closest('.remove-favorite')) {
            e.preventDefault();
            const gameCard = e.target.closest('.game-card');
            if (!gameCard) return;
            
            const gameId = gameCard.getAttribute('data-game-id');
            const gameTitle = gameCard.querySelector('.game-title')?.textContent || '游戏';
            
            // 确认删除
            if (confirm(`确定要从收藏中移除"${gameTitle}"吗？`)) {
                // 添加删除动画
                gameCard.classList.add('removing');
                
                // 模拟API请求
                setTimeout(function() {
                    gameCard.remove();
                    
                    // 显示成功消息
                    showMessage(`"${gameTitle}" 已从收藏中移除`, 'success');
                    
                    // 如果没有收藏游戏了，显示空状态
                    if (favoritesList.querySelectorAll('.game-card').length === 0) {
                        if (emptyFavorites) {
                            emptyFavorites.classList.remove('d-none');
                        }
                    }
                    
                    // 更新收藏数量
                    updateFavoritesCount(-1);
                }, 500);
            }
        }
    });
    
    // 排序收藏游戏
    const sortSelect = document.getElementById('sort-favorites');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const games = Array.from(favoritesList.querySelectorAll('.game-card'));
            if (games.length <= 1) return;
            
            // 根据选择的排序方式排序
            games.sort((a, b) => {
                switch (this.value) {
                    case 'name-asc':
                        return a.querySelector('.game-title').textContent.localeCompare(
                            b.querySelector('.game-title').textContent
                        );
                    case 'name-desc':
                        return b.querySelector('.game-title').textContent.localeCompare(
                            a.querySelector('.game-title').textContent
                        );
                    case 'date-added-desc':
                        return new Date(b.getAttribute('data-date-added')) - 
                               new Date(a.getAttribute('data-date-added'));
                    case 'date-added-asc':
                        return new Date(a.getAttribute('data-date-added')) - 
                               new Date(b.getAttribute('data-date-added'));
                    case 'rating-desc':
                        return parseFloat(b.getAttribute('data-rating') || 0) - 
                               parseFloat(a.getAttribute('data-rating') || 0);
                    case 'rating-asc':
                        return parseFloat(a.getAttribute('data-rating') || 0) - 
                               parseFloat(b.getAttribute('data-rating') || 0);
                    default:
                        return 0;
                }
            });
            
            // 重新排列DOM元素
            games.forEach(game => favoritesList.appendChild(game));
            
            // 添加排序动画
            favoritesList.classList.add('sorting');
            setTimeout(() => {
                favoritesList.classList.remove('sorting');
            }, 500);
        });
    }
}

/**
 * 更新收藏游戏数量
 */
function updateFavoritesCount(change) {
    const countElement = document.querySelector('.favorites-count');
    if (countElement) {
        const currentCount = parseInt(countElement.textContent, 10) || 0;
        countElement.textContent = Math.max(0, currentCount + change);
    }
}

/**
 * 初始化游戏历史记录功能
 */
function initGameHistory() {
    const historyList = document.querySelector('.history-list');
    const clearHistoryBtn = document.getElementById('clear-history');
    
    if (!historyList) return;
    
    // 清空历史记录
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', function() {
            if (confirm('确定要清空所有游戏历史记录吗？此操作无法撤销。')) {
                // 添加淡出动画
                const historyItems = historyList.querySelectorAll('.history-item');
                historyItems.forEach(item => {
                    item.classList.add('removing');
                });
                
                // 模拟API请求
                setTimeout(function() {
                    historyList.innerHTML = '<div class="empty-history text-center py-5"><p class="text-muted">暂无游戏历史记录</p></div>';
                    showMessage('游戏历史记录已清空', 'success');
                }, 500);
            }
        });
    }
    
    // 单个删除历史记录
    historyList.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-history') || e.target.closest('.remove-history')) {
            e.preventDefault();
            const historyItem = e.target.closest('.history-item');
            if (!historyItem) return;
            
            const gameTitle = historyItem.querySelector('.game-title')?.textContent || '游戏';
            
            // 添加删除动画
            historyItem.classList.add('removing');
            
            // 模拟API请求
            setTimeout(function() {
                historyItem.remove();
                showMessage(`"${gameTitle}" 的历史记录已删除`, 'success');
                
                // 如果没有历史记录了，显示空状态
                if (historyList.querySelectorAll('.history-item').length === 0) {
                    historyList.innerHTML = '<div class="empty-history text-center py-5"><p class="text-muted">暂无游戏历史记录</p></div>';
                }
            }, 500);
        }
    });
}

/**
 * 初始化消息通知功能
 */
function initNotifications() {
    const notificationsList = document.querySelector('.notifications-list');
    const markAllReadBtn = document.getElementById('mark-all-read');
    
    if (!notificationsList) return;
    
    // 标记所有通知为已读
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            const unreadNotifications = notificationsList.querySelectorAll('.notification-item.unread');
            if (unreadNotifications.length === 0) return;
            
            // 模拟API请求
            markAllReadBtn.disabled = true;
            markAllReadBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
            
            setTimeout(function() {
                unreadNotifications.forEach(notification => {
                    notification.classList.remove('unread');
                });
                
                markAllReadBtn.disabled = false;
                markAllReadBtn.textContent = '全部标为已读';
                
                // 更新通知计数
                updateNotificationCount(0);
                
                showMessage('所有通知已标记为已读', 'success');
            }, 1000);
        });
    }
    
    // 标记单个通知为已读
    notificationsList.addEventListener('click', function(e) {
        if (e.target.classList.contains('notification-item') || e.target.closest('.notification-item')) {
            const notificationItem = e.target.closest('.notification-item');
            if (!notificationItem || !notificationItem.classList.contains('unread')) return;
            
            // 标记为已读
            notificationItem.classList.remove('unread');
            
            // 更新通知计数
            updateNotificationCount(-1);
        }
    });
}

/**
 * 更新通知计数
 */
function updateNotificationCount(change) {
    const countElement = document.querySelector('.notification-count');
    if (!countElement) return;
    
    if (change === 0) {
        // 全部标为已读
        countElement.textContent = '0';
        document.querySelectorAll('.notification-badge').forEach(badge => {
            badge.classList.add('d-none');
        });
    } else {
        // 增加或减少计数
        const currentCount = parseInt(countElement.textContent, 10) || 0;
        const newCount = Math.max(0, currentCount + change);
        countElement.textContent = newCount;
        
        // 更新通知徽章显示
        document.querySelectorAll('.notification-badge').forEach(badge => {
            if (newCount > 0) {
                badge.textContent = newCount;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        });
    }
}

/**
 * 初始化用户设置功能
 */
function initUserSettings() {
    const settingsForm = document.getElementById('settings-form');
    const saveSettingsBtn = document.querySelector('.save-settings-btn');
    
    if (!settingsForm) return;
    
    settingsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const formData = new FormData(settingsForm);
        const settings = {
            emailNotifications: formData.get('email-notifications') === 'on',
            siteNotifications: formData.get('site-notifications') === 'on',
            privateProfile: formData.get('private-profile') === 'on',
            language: formData.get('language'),
            theme: formData.get('theme')
        };
        
        // 显示加载状态
        saveSettingsBtn.disabled = true;
        saveSettingsBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 保存中...';
        
        // 模拟API请求
        setTimeout(function() {
            console.log('保存的设置:', settings);
            
            // 应用主题更改
            if (settings.theme) {
                document.body.dataset.theme = settings.theme;
                localStorage.setItem('theme', settings.theme);
            }
            
            // 恢复按钮状态
            saveSettingsBtn.disabled = false;
            saveSettingsBtn.textContent = '保存设置';
            
            // 显示成功消息
            showMessage('设置已保存', 'success');
        }, 1000);
    });
    
    // 密码修改表单
    const passwordForm = document.getElementById('password-form');
    const savePasswordBtn = document.querySelector('.save-password-btn');
    
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            // 验证表单
            if (!currentPassword || !newPassword || !confirmPassword) {
                showMessage('请填写所有密码字段', 'danger');
                return;
            }
            
            if (newPassword !== confirmPassword) {
                showMessage('新密码与确认密码不匹配', 'danger');
                return;
            }
            
            if (newPassword.length < 8) {
                showMessage('新密码长度必须至少为8个字符', 'danger');
                return;
            }
            
            // 显示加载状态
            savePasswordBtn.disabled = true;
            savePasswordBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 保存中...';
            
            // 模拟API请求
            setTimeout(function() {
                // 恢复按钮状态
                savePasswordBtn.disabled = false;
                savePasswordBtn.textContent = '修改密码';
                
                // 清空表单
                passwordForm.reset();
                
                // 显示成功消息
                showMessage('密码已成功修改！', 'success');
            }, 1500);
        });
    }
}

/**
 * 初始化标签页切换
 */
function initTabSwitching() {
    const tabButtons = document.querySelectorAll('.profile-tab-btn');
    const tabContents = document.querySelectorAll('.profile-tab-content');
    
    if (tabButtons.length === 0 || tabContents.length === 0) return;
    
    // 标签页切换
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetTab = this.getAttribute('data-target');
            if (!targetTab) return;
            
            // 激活当前按钮
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 显示对应内容
            tabContents.forEach(content => {
                content.classList.remove('active');
                content.classList.add('d-none');
            });
            
            const tabContent = document.querySelector(targetTab);
            if (tabContent) {
                tabContent.classList.add('active');
                tabContent.classList.remove('d-none');
            }
            
            // 保存到URL
            history.pushState(null, '', `#${targetTab.substring(1)}`);
        });
    });
    
    // 根据URL显示初始标签页
    const handleHashChange = () => {
        const hash = window.location.hash;
        if (hash) {
            const targetButton = document.querySelector(`.profile-tab-btn[data-target="#${hash.substring(1)}"]`);
            if (targetButton) {
                targetButton.click();
                return;
            }
        }
        
        // 默认显示第一个标签页
        tabButtons[0]?.click();
    };
    
    // 初始加载和URL变化时处理
    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
}

// 获取随机头像按钮点击事件
getRandomAvatarsBtn.addEventListener('click', function() {
    // 显示头像网格
    randomAvatarGrid.classList.remove('d-none');
    
    // 生成随机头像
    const avatarOptions = document.querySelectorAll('.random-avatar-option');
    
    // 从 randomuser.me 生成随机头像
    const genders = ['men', 'women'];
    
    avatarOptions.forEach((img, index) => {
        const gender = genders[Math.floor(Math.random() * genders.length)];
        const randomId = Math.floor(Math.random() * 99) + 1; // 1-99
        const avatarUrl = `https://randomuser.me/api/portraits/${gender}/${randomId}.jpg`;
        
        img.src = avatarUrl;
        img.dataset.url = avatarUrl;
        
        // 添加点击事件
        img.addEventListener('click', function() {
            // 更新预览
            avatarPreview.src = this.dataset.url;
            
            // 设置隐藏字段的值
            selectedRandomAvatarInput.value = this.dataset.url;
            
            // 高亮选中的头像
            avatarOptions.forEach(opt => opt.classList.remove('selected-avatar'));
            this.classList.add('selected-avatar');
        });
    });
}); 