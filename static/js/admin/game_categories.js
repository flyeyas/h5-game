/**
 * 游戏分类管理模块
 * 处理分类的添加、编辑、查看、删除和状态切换等操作
 */

// 图标数据
const solidIcons = [
    // 游戏相关图标
    'gamepad', 'dice', 'dice-d6', 'dice-d20', 'chess', 'chess-board', 'puzzle-piece', 'vr-cardboard',
    'trophy', 'medal', 'award', 'crown', 'ghost', 'robot', 'rocket', 'space-shuttle', 'jedi', 'wand-magic-sparkles',
    'hat-wizard', 'dragon', 'swords', 'bow-arrow', 'scroll', 'skull-crossbones', 'fort-awesome',
    'crosshairs', 'gun', 'shield-alt', 'shield-virus', 'dungeon', 'landmark', 'radar', 'joystick',
    'controller', 'headset', 'coins', 'gem', 'treasure-chest', 'fire', 'bolt', 'meteor', 'football',
    'basketball-ball', 'baseball-ball', 'volleyball-ball', 'futbol', 'hockey-puck', 'table-tennis',
    
    // 常用图标
    'home', 'user', 'users', 'star', 'heart', 'bookmark', 'check', 'times', 'cog', 'cogs',
    'folder', 'file', 'image', 'video', 'music', 'film', 'book', 'map', 'map-marker-alt',
    'calendar', 'clock', 'search', 'bell', 'envelope', 'comment', 'shopping-cart', 'dollar-sign',
    'exclamation-circle', 'info-circle', 'question-circle', 'check-circle', 'times-circle',
    'thumbs-up', 'thumbs-down', 'chart-bar', 'chart-line', 'chart-pie', 'chart-area',
    'mobile', 'tablet', 'laptop', 'desktop', 'server', 'cloud', 'database', 'code',
    'keyboard', 'microchip', 'download', 'upload', 'sync', 'link', 'wifi', 'bluetooth',
    'lock', 'unlock', 'key', 'eye', 'eye-slash', 'tag', 'tags', 'copy', 'cut', 'paste',
    'save', 'print', 'camera', 'video-camera', 'microphone', 'headphones', 'volume-up',
    'phone', 'sms', 'address-book', 'id-card', 'credit-card', 'qrcode', 'barcode',
    'car', 'truck', 'bus', 'train', 'plane', 'bicycle', 'motorcycle', 'ship', 'rocket',
    'utensils', 'coffee', 'beer', 'wine-glass', 'pizza-slice', 'hamburger', 'cookie',
    'apple-alt', 'carrot', 'bread-slice', 'cheese', 'ice-cream', 'candy-cane',
    'store', 'shopping-bag', 'shopping-basket', 'cash-register', 'receipt',
    'box', 'box-open', 'archive', 'gift', 'gifts', 'birthday-cake',
    'brush', 'paint-brush', 'palette', 'pencil-alt', 'pen', 'pen-alt', 'pen-fancy',
    'signature', 'highlighter', 'marker', 'eraser', 'ruler', 'compass',
    'paperclip', 'paper-plane', 'sticky-note', 'envelope-open', 'envelope-open-text',
    'comments', 'comment-alt', 'comment-dots', 'comment-medical', 'comment-slash',
    'suitcase', 'briefcase', 'backpack', 'graduation-cap', 'school', 'university',
    'globe', 'globe-americas', 'globe-asia', 'globe-europe', 'globe-africa',
    'flag', 'map-pin', 'thumbtack', 'route', 'directions', 'compass',
    'running', 'walking', 'biking', 'hiking', 'swimming', 'skating', 'skiing',
    'dumbbell', 'weight', 'heartbeat', 'medkit', 'first-aid', 'pills', 'prescription-bottle',
    'stethoscope', 'user-md', 'user-nurse', 'hospital', 'clinic-medical', 'ambulance',
    'child', 'baby', 'baby-carriage', 'people-arrows', 'people-carry', 'person-booth',
    'cat', 'dog', 'hippo', 'fish', 'frog', 'spider', 'kiwi-bird', 'horse', 'horse-head',
    'paw', 'bone', 'feather', 'crow', 'dragon', 'otter', 'narwhal', 'rabbit',
    'seedling', 'tree', 'leaf', 'spa', 'plant', 'flower', 'holly-berry', 'cannabis',
    'sun', 'moon', 'cloud-sun', 'cloud-moon', 'cloud-rain', 'cloud-showers-heavy',
    'temperature-high', 'temperature-low', 'wind', 'snowflake', 'umbrella',
    'mountain', 'volcano', 'desert', 'island-tropical', 'wave-square'
];

const regularIcons = [
    'address-book', 'address-card', 'bell', 'bookmark', 'building', 'calendar', 'chart-bar', 
    'clipboard', 'clock', 'comment', 'comments', 'compass', 'copy', 'credit-card', 
    'envelope', 'eye', 'file', 'file-alt', 'folder', 'folder-open', 'frown', 'heart', 
    'hospital', 'hourglass', 'id-badge', 'id-card', 'image', 'images', 'keyboard', 
    'lemon', 'life-ring', 'lightbulb', 'map', 'moon', 'newspaper', 'paper-plane', 
    'pause-circle', 'play-circle', 'question-circle', 'save', 'share-square', 'smile', 
    'snowflake', 'square', 'star', 'sticky-note', 'stop-circle', 'sun', 'thumbs-down', 
    'thumbs-up', 'user', 'user-circle', 'window-close', 'window-maximize', 'window-minimize', 
    'window-restore'
];

const brandIcons = [
    'android', 'apple', 'chrome', 'discord', 'edge', 'facebook', 'firefox', 'github', 
    'google', 'instagram', 'js', 'linux', 'node', 'npm', 'paypal', 'php', 'pinterest', 
    'playstation', 'python', 'react', 'steam', 'twitch', 'twitter', 'ubuntu', 'vimeo', 
    'weibo', 'whatsapp', 'wikipedia-w', 'windows', 'wordpress', 'xbox', 'youtube',
    'aws', 'bluetooth', 'bootstrap', 'css3', 'docker', 'dribbble', 'dropbox', 'drupal',
    'ethereum', 'font-awesome', 'font-awesome-flag', 'font-awesome-alt', 'git', 'git-alt',
    'gitlab', 'html5', 'jira', 'kickstarter', 'less', 'linkedin', 'mailchimp', 'microsoft',
    'opencart', 'sass', 'shopify', 'slack', 'snapchat', 'spotify', 'stack-overflow',
    'telegram', 'tiktok', 'tumblr', 'unity', 'unsplash', 'viber', 'wix', 'yarn'
];

/**
 * 清除搜索框内容并提交表单
 */
function clearSearch() {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.delete('search');
    urlParams.set('page', 1); // 重置到第一页
    window.location.search = urlParams.toString();
}

/**
 * 根据状态过滤分类列表
 * @param {string} status 状态值：''全部，'active'已启用，'inactive'已禁用
 */
function filterByStatus(status) {
    const urlParams = new URLSearchParams(window.location.search);
    if (status) {
        urlParams.set('status', status);
    } else {
        urlParams.delete('status');
    }
    urlParams.set('page', 1); // 切换筛选条件时，回到第一页
    window.location.search = urlParams.toString();
}

/**
 * 更改每页显示数量
 * @param {number} size 每页显示的记录数
 */
function changePageSize(size) {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set('page_size', size);
    urlParams.set('page', 1); // 切换每页显示数量时，回到第一页
    window.location.search = urlParams.toString();
}

/**
 * 获取CSRF Token
 * @returns {string} CSRF令牌值
 */
function getCsrfToken() {
    return $('[name=csrfmiddlewaretoken]').val();
}

/**
 * 显示消息提示框
 * @param {string} type 消息类型：'success'成功，'error'错误
 * @param {string} message 消息内容
 */
function showToast(type, message) {
    const toastContainer = $('#toast-container');
    const toast = $(`
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `);
    
    toastContainer.append(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // 自动移除
    toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

/**
 * 编辑分类
 * @param {number} categoryId 分类ID
 */
function editCategory(categoryId) {
    // 通过Ajax获取分类详情
    $.ajax({
        url: `/admin/game-categories/detail/${categoryId}/`,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            if (data.status === 'success') {
                const category = data.category;
                // 填充表单
                $('#edit-category-id').val(category.id);
                $('#edit-category-name').val(category.name);
                $('#edit-category-description').val(category.description);
                $('#edit-category-parent').val(category.parent_id || '');
                $('#edit-category-order').val(category.order);
                $('#edit-category-slug').val(category.slug);
                $('#edit-category-color').val(category.color);
                $('#edit-category-is-active').prop('checked', category.is_active);
                
                // 设置图标
                $('#edit-category-icon').val(category.icon || 'fas fa-gamepad');
                $('#edit-icon-preview').attr('class', category.icon || 'fas fa-gamepad');
                
                // 显示模态框
                $('#editCategoryModal').modal('show');
            } else {
                showToast('error', data.message || '获取分类详情失败');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
            showToast('error', '加载分类数据时出错');
        }
    });
}

/**
 * 查看分类详情
 * @param {number} categoryId 分类ID
 */
function viewCategory(categoryId) {
    // 通过Ajax获取分类详情
    $.ajax({
        url: `/admin/game-categories/detail/${categoryId}/`,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            if (data.status === 'success') {
                const category = data.category;
                // 填充详情模态框
                $('#view-category-name').text(category.name);
                $('#view-category-description').text(category.description || '暂无描述');
                $('#view-category-parent').text(category.parent_id ? '有父级分类' : '无 (顶级分类)');
                $('#view-category-order').text(category.order);
                $('#view-category-slug').text(category.slug || '无');
                $('#view-category-color').css('backgroundColor', category.color);
                $('#view-category-color-code').text(category.color);
                $('#view-category-status').text(category.is_active ? '已启用' : '已禁用');
                $('#view-category-status').attr('class', category.is_active ? 'badge bg-success' : 'badge bg-secondary');
                
                // 显示图标
                if (category.icon) {
                    $('#view-category-icon').attr('class', category.icon);
                    $('#view-category-icon-class').text(category.icon);
                } else {
                    $('#view-category-icon').attr('class', 'fas fa-gamepad');
                    $('#view-category-icon-class').text('fas fa-gamepad (默认)');
                }
                
                // 显示模态框
                $('#viewCategoryModal').modal('show');
            } else {
                showToast('error', data.message || '获取分类详情失败');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
            showToast('error', '加载分类数据时出错');
        }
    });
}

/**
 * 切换分类状态
 * @param {number} categoryId 分类ID
 */
function toggleCategoryStatus(categoryId) {
    // 通过Ajax获取分类详情，然后显示确认模态框
    $.ajax({
        url: `/admin/game-categories/detail/${categoryId}/`,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            if (data.status === 'success') {
                const category = data.category;
                
                // 设置模态框内容
                $('#toggle-category-id').val(category.id);
                $('#toggle-category-name').text(category.name);
                
                // 设置当前状态和新状态
                const currentStatus = category.is_active ? '已启用' : '已禁用';
                const newStatus = category.is_active ? '禁用' : '启用';
                $('#toggle-category-current-status').html(`<span class="badge ${category.is_active ? 'bg-success' : 'bg-secondary'}">${currentStatus}</span>`);
                $('#toggle-category-new-status').html(`<span class="badge ${category.is_active ? 'bg-secondary' : 'bg-success'}">${newStatus}</span>`);
                
                // 更新确认消息
                $('#toggle-status-message').text(`您确定要${newStatus}分类"${category.name}"吗？`);
                
                // 显示模态框
                $('#toggleStatusModal').modal('show');
            } else {
                showToast('error', data.message || '获取分类详情失败');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
            showToast('error', '加载分类数据时出错');
        }
    });
}

/**
 * 执行分类状态切换
 * @param {number} categoryId 分类ID
 */
function executeToggleCategoryStatus(categoryId) {
    $.ajax({
        url: `/admin/game-categories/toggle-status/${categoryId}/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        dataType: 'json',
        success: function(data) {
            if (data.status === 'success') {
                showToast('success', data.message);
                
                // 关闭模态框
                $('#toggleStatusModal').modal('hide');
                
                // 刷新页面
                setTimeout(function() {
                    window.location.reload();
                }, 1000);
            } else {
                showToast('error', data.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
            showToast('error', '更改状态时发生错误');
        }
    });
}

/**
 * 确认删除分类
 * @param {number} categoryId 分类ID
 * @param {string} categoryName 分类名称
 */
function confirmDeleteCategory(categoryId, categoryName) {
    $('#delete-category-id').val(categoryId);
    $('#delete-category-name').text(categoryName);
    $('#deleteCategoryModal').modal('show');
}

/**
 * 加载图标集
 * @param {string} container 容器选择器
 * @param {Array} icons 图标数组
 * @param {string} prefix 图标前缀
 */
function loadIconSet(container, icons, prefix) {
    const $container = $(container);
    
    // 清除加载指示器
    $container.empty();
    
    // 添加图标
    icons.forEach(function(icon) {
        const $item = $(`
            <div class="col">
                <div class="icon-item text-center" data-icon="${prefix} fa-${icon}">
                    <i class="${prefix} fa-${icon}"></i>
                    <div class="icon-name">${icon}</div>
                </div>
            </div>
        `);
        
        $container.append($item);
    });
}

/**
 * 加载图标
 */
function loadIcons() {
    // 检查是否已加载
    if ($('.solid-icons').children().length <= 1) {
        // 移除加载指示器
        $('.solid-icons').empty();
        
        // 加载实心图标
        loadIconSet('.solid-icons', solidIcons, 'fas');
    }
    
    // 检查是否已加载
    if ($('.regular-icons').children().length === 0) {
        // 加载线条图标
        loadIconSet('.regular-icons', regularIcons, 'far');
    }
    
    // 检查是否已加载
    if ($('.brand-icons').children().length === 0) {
        // 加载品牌图标
        loadIconSet('.brand-icons', brandIcons, 'fab');
    }
}

/**
 * 初始化游戏分类管理功能
 */
$(document).ready(function() {
    // 设置颜色框背景色
    $('.category-color-box').each(function() {
        const color = $(this).data('color');
        if (color) {
            $(this).css('backgroundColor', color);
        }
    });
    
    // 为编辑按钮添加点击事件
    $('.edit-category-btn').on('click', function() {
        const categoryId = $(this).data('id');
        editCategory(categoryId);
    });
    
    // 为查看按钮添加点击事件
    $('.view-category-btn').on('click', function() {
        const categoryId = $(this).data('id');
        viewCategory(categoryId);
    });
    
    // 为状态切换按钮添加点击事件
    $('.toggle-status-btn').on('click', function() {
        const categoryId = $(this).data('id');
        toggleCategoryStatus(categoryId);
    });
    
    // 为状态切换确认按钮添加点击事件
    $('#confirm-toggle-status').on('click', function() {
        const categoryId = $('#toggle-category-id').val();
        executeToggleCategoryStatus(categoryId);
    });
    
    // 为删除按钮添加点击事件
    $('.delete-category-btn').on('click', function() {
        const categoryId = $(this).data('id');
        const categoryName = $(this).data('name');
        confirmDeleteCategory(categoryId, categoryName);
    });
    
    // 为添加分类表单添加提交事件 - 使用jQuery和Ajax实现前后端交互
    $('#add-category-form').on('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const formData = new FormData(this);
        
        // 确保复选框值正确传递
        const isActive = $('#add-category-is-active').is(':checked');
        formData.set('is_active', isActive ? 'true' : 'false');
        
        $.ajax({
            url: '/admin/game-categories/create/',
            type: 'POST',
            data: formData,
            processData: false,  // 不处理数据
            contentType: false,  // 不设置内容类型
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            success: function(data) {
                if (data.status === 'success') {
                    showToast('success', data.message);
                    
                    // 关闭模态框
                    $('#addCategoryModal').modal('hide');
                    
                    // 重置表单
                    $('#add-category-form')[0].reset();
                    
                    // 刷新页面
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('error', data.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                let errorMessage = '提交表单时发生错误';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                showToast('error', errorMessage);
            }
        });
    });
    
    // 为编辑分类表单添加提交事件
    $('#edit-category-form').on('submit', function(e) {
        e.preventDefault();
        
        // 获取分类ID和表单数据
        const categoryId = $('#edit-category-id').val();
        const formData = new FormData(this);
        
        // 确保复选框值正确传递
        const isActive = $('#edit-category-is-active').is(':checked');
        formData.set('is_active', isActive ? 'true' : 'false');
        
        $.ajax({
            url: `/admin/game-categories/update/${categoryId}/`,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            success: function(data) {
                if (data.status === 'success') {
                    showToast('success', data.message);
                    
                    // 关闭模态框
                    $('#editCategoryModal').modal('hide');
                    
                    // 刷新页面
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('error', data.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                let errorMessage = '提交表单时发生错误';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                showToast('error', errorMessage);
            }
        });
    });
    
    // 为删除分类表单添加提交事件
    $('#delete-category-form').on('submit', function(e) {
        e.preventDefault();
        
        const categoryId = $('#delete-category-id').val();
        
        $.ajax({
            url: `/admin/game-categories/delete/${categoryId}/`,
            type: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            dataType: 'json',
            success: function(data) {
                if (data.status === 'success') {
                    showToast('success', data.message);
                    
                    // 关闭模态框
                    $('#deleteCategoryModal').modal('hide');
                    
                    // 刷新页面
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('error', data.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                let errorMessage = '删除分类时发生错误';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                showToast('error', errorMessage);
            }
        });
    });

    // 当图标选择器模态框打开时
    $('#iconPickerModal').on('show.bs.modal', function(event) {
        const button = $(event.relatedTarget);
        const targetField = button.data('target-field');
        const previewElement = button.data('preview-element');
        
        // 存储目标字段和预览元素ID
        $(this).data('target-field', targetField);
        $(this).data('preview-element', previewElement);
        
        // 加载图标
        loadIcons();
    });

    // 图标搜索
    $('#icon-search').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        
        // 搜索所有图标
        $('.icon-grid .icon-item').each(function() {
            const iconName = $(this).find('.icon-name').text().toLowerCase();
            
            if (iconName.includes(searchTerm)) {
                $(this).parent().show();
            } else {
                $(this).parent().hide();
            }
        });
    });

    // 图标预览更新 - 添加表单
    $('#add-category-icon').on('input', function() {
        const iconClass = $(this).val();
        // 先移除旧图标
        $('#add-icon-preview').parent().empty().html('<i id="add-icon-preview"></i>');
        // 设置新图标类
        if (iconClass) {
            $('#add-icon-preview').attr('class', iconClass);
        } else {
            $('#add-icon-preview').attr('class', 'fas fa-gamepad');
        }
    });

    // 图标预览更新 - 编辑表单
    $('#edit-category-icon').on('input', function() {
        const iconClass = $(this).val();
        // 先移除旧图标
        $('#edit-icon-preview').parent().empty().html('<i id="edit-icon-preview"></i>');
        // 设置新图标类
        if (iconClass) {
            $('#edit-icon-preview').attr('class', iconClass);
        } else {
            $('#edit-icon-preview').attr('class', 'fas fa-gamepad');
        }
    });
    
    // 使用事件委托处理图标选择
    $(document).on('click', '.icon-item', function() {
        const iconClass = $(this).data('icon');
        
        // 移除之前的选中状态
        $('.icon-item').removeClass('selected');
        
        // 添加选中状态
        $(this).addClass('selected');
        
        // 获取目标字段和预览元素
        const targetField = $('#iconPickerModal').data('target-field');
        const previewElement = $('#iconPickerModal').data('preview-element');
        
        // 设置字段值
        $(`#${targetField}`).val(iconClass);
        
        // 更新预览元素 - 先移除旧图标，再添加新图标
        $(`#${previewElement}`).parent().empty().html(`<i id="${previewElement}"></i>`);
        $(`#${previewElement}`).attr('class', iconClass);
        
        // 关闭模态框
        $('#iconPickerModal').modal('hide');
    });
    
    // 初始化时确保图标预览正确显示
    $('#add-category-icon, #edit-category-icon').each(function() {
        const iconClass = $(this).val();
        const previewId = $(this).attr('id') === 'add-category-icon' ? 'add-icon-preview' : 'edit-icon-preview';
        if (iconClass) {
            $(`#${previewId}`).attr('class', iconClass);
        }
    });
});