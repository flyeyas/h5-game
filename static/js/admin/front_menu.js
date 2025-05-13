// 前台菜单管理JavaScript
$(document).ready(function() {
    // 初始化图标预览功能
    initIconPreview();
    
    // 初始化表单验证
    initFormValidation();
    
    // 初始化添加菜单
    initAddMenu();
    
    // 初始化编辑菜单
    initEditMenu();
    
    // 初始化删除菜单
    initDeleteMenu();
    
    // 初始化菜单排序功能
    initMenuSorting();
});

/**
 * 初始化图标预览功能
 */
function initIconPreview() {
    // 添加菜单模态框中的图标预览
    $('#id_icon').on('input', function() {
        updateIconPreview($(this).val(), '#icon-preview');
    });
    
    // 编辑菜单模态框中的图标预览
    $('#edit_icon').on('input', function() {
        updateIconPreview($(this).val(), '#edit_icon_preview');
    });
}

/**
 * 更新图标预览
 * @param {string} iconClass - 图标类名
 * @param {string} previewSelector - 预览元素选择器
 */
function updateIconPreview(iconClass, previewSelector) {
    if (iconClass) {
        $(previewSelector).attr('class', iconClass);
        $(previewSelector).css('font-size', '14px'); // 设置更小的图标尺寸
    } else {
        $(previewSelector).attr('class', 'fas fa-gear'); // 默认图标
        $(previewSelector).css('font-size', '14px'); // 设置更小的图标尺寸
    }
}

/**
 * 初始化表单验证
 */
function initFormValidation() {
    // 表单验证函数，用于添加和编辑菜单
    function validateMenuForm(form) {
        let isValid = true;
        
        // 检查必填字段
        $(form).find('[required]').each(function() {
            if (!$(this).val().trim()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        return isValid;
    }
    
    // 添加表单验证
    $('#menuForm').on('submit', function(event) {
        event.preventDefault();
        if (validateMenuForm(this)) {
            submitMenuForm($(this));
        }
    });
    
    // 编辑表单验证
    $('#editMenuForm').on('submit', function(event) {
        event.preventDefault();
        if (validateMenuForm(this)) {
            submitEditForm($(this));
        }
    });
}

/**
 * 初始化添加菜单
 */
function initAddMenu() {
    // 打开添加菜单模态框时重置表单
    $('#addMenuModal').on('show.bs.modal', function() {
        $('#menuForm')[0].reset();
        $('#formAlerts').empty();
        $('#icon-preview').attr('class', 'fas fa-gear');
        $('#menuForm').find('.is-invalid').removeClass('is-invalid');
    });
}

/**
 * 提交添加菜单表单
 * @param {jQuery} $form - 表单jQuery对象
 */
function submitMenuForm($form) {
    // 显示加载状态
    const $submitBtn = $('#submitMenuForm');
    $submitBtn.prop('disabled', true);
    $submitBtn.find('.spinner-border').removeClass('d-none');
    
    $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: $form.serialize(),
        dataType: 'json',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            if (response.status === 'success') {
                // 成功添加
                $('#addMenuModal').modal('hide');
                
                // 显示成功提示
                $('#successMessage').text(response.message || '前台菜单添加成功');
                $('#successModal').modal('show');
                
                // 成功模态框关闭后刷新页面
                $('#successModal').on('hidden.bs.modal', function() {
                    window.location.reload();
                });
            } else {
                // 显示错误信息
                showFormAlert($('#formAlerts'), 'danger', response.message || '添加菜单失败，请重试');
                
                // 如果有字段错误，显示字段错误
                if (response.errors) {
                    for (const field in response.errors) {
                        const input = $('#id_' + field);
                        if (input.length) {
                            input.addClass('is-invalid');
                            const feedback = input.siblings('.invalid-feedback');
                            if (feedback.length) {
                                feedback.text(response.errors[field][0]);
                            }
                        }
                    }
                }
            }
        },
        error: function(xhr, status, error) {
            console.error('添加菜单失败:', error);
            let errorMsg = '服务器错误，请重试';
            try {
                const response = JSON.parse(xhr.responseText);
                errorMsg = response.message || errorMsg;
            } catch(e) {}
            
            showFormAlert($('#formAlerts'), 'danger', errorMsg);
        },
        complete: function() {
            // 恢复按钮状态
            $submitBtn.prop('disabled', false);
            $submitBtn.find('.spinner-border').addClass('d-none');
        }
    });
}

/**
 * 初始化编辑菜单
 */
function initEditMenu() {
    // 编辑菜单按钮点击事件
    $('.edit-menu-btn').on('click', function() {
        const menuId = $(this).data('menu-id');
        loadMenuData(menuId);
    });
    
    // 打开编辑模态框时重置状态
    $('#editMenuModal').on('show.bs.modal', function() {
        $('#editFormContent').hide();
        $('#editFormLoading').show();
        $('#editFormAlerts').empty();
    });
    
    // 加载菜单数据
    function loadMenuData(menuId) {
        $.ajax({
            url: `/admin/frontend/menu/detail/${menuId}/`,
            type: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            dataType: 'json',
            success: function(response) {
                if (response.status === 'success') {
                    fillEditForm(response.menu);
                } else {
                    $('#editFormLoading').hide();
                    showFormAlert($('#editFormAlerts'), 'danger', response.message || '加载菜单数据失败');
                    $('#editFormContent').show();
                }
            },
            error: function(xhr, status, error) {
                console.error('加载菜单数据失败:', error);
                let errorMsg = '服务器错误，请重试';
                try {
                    const response = JSON.parse(xhr.responseText);
                    errorMsg = response.message || errorMsg;
                } catch(e) {}
                
                $('#editFormLoading').hide();
                showFormAlert($('#editFormAlerts'), 'danger', errorMsg);
                $('#editFormContent').show();
            }
        });
    }
    
    // 填充编辑表单
    function fillEditForm(menu) {
        $('#edit_menu_id').val(menu.id);
        $('#edit_name').val(menu.name);
        $('#edit_url').val(menu.url);
        $('#edit_icon').val(menu.icon || '');
        $('#edit_order').val(menu.order);
        $('#edit_is_active').prop('checked', menu.is_active);
        $('#edit_is_external').prop('checked', menu.is_external);
        
        // 设置父菜单
        if (menu.parent) {
            $('#edit_parent').val(menu.parent);
        } else {
            $('#edit_parent').val('');
        }
        
        // 更新图标预览
        updateIconPreview(menu.icon, '#edit_icon_preview');
        
        // 对当前菜单的子菜单禁用选择父菜单为自己
        $('#edit_parent option').prop('disabled', false);
        if (menu.children && menu.children.length > 0) {
            menu.children.forEach(function(childId) {
                $('#edit_parent option[value="' + childId + '"]').prop('disabled', true);
            });
        }
        // 禁止选择自己作为父菜单
        $('#edit_parent option[value="' + menu.id + '"]').prop('disabled', true);
        
        // 显示表单内容
        $('#editFormLoading').hide();
        $('#editFormContent').show();
    }
}

/**
 * 提交编辑表单
 * @param {jQuery} $form - 表单jQuery对象
 */
function submitEditForm($form) {
    const menuId = $('#edit_menu_id').val();
    
    // 显示加载状态
    const $submitBtn = $('#submitEditForm');
    $submitBtn.prop('disabled', true);
    
    $.ajax({
        url: `/admin/frontend/menu/edit/${menuId}/`,
        type: 'POST',
        data: $form.serialize(),
        dataType: 'json',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            if (response.status === 'success') {
                // 关闭编辑模态框
                $('#editMenuModal').modal('hide');
                
                // 显示成功提示
                $('#successMessage').text(response.message || '前台菜单修改成功');
                $('#successModal').modal('show');
                
                // 成功模态框关闭后刷新页面
                $('#successModal').on('hidden.bs.modal', function() {
                    window.location.reload();
                });
            } else {
                // 显示错误信息
                showFormAlert($('#editFormAlerts'), 'danger', response.message || '更新菜单失败，请重试');
                
                // 如果有字段错误，显示字段错误
                if (response.errors) {
                    for (const field in response.errors) {
                        const input = $('#edit_' + field);
                        if (input.length) {
                            input.addClass('is-invalid');
                            const feedback = input.siblings('.invalid-feedback');
                            if (feedback.length) {
                                feedback.text(response.errors[field][0]);
                            }
                        }
                    }
                }
            }
        },
        error: function(xhr, status, error) {
            console.error('更新菜单失败:', error);
            let errorMsg = '服务器错误，请重试';
            try {
                const response = JSON.parse(xhr.responseText);
                errorMsg = response.message || errorMsg;
            } catch(e) {}
            
            showFormAlert($('#editFormAlerts'), 'danger', errorMsg);
        },
        complete: function() {
            // 恢复按钮状态
            $submitBtn.prop('disabled', false);
        }
    });
}

/**
 * 初始化删除菜单
 */
function initDeleteMenu() {
    // 监听删除模态框打开事件，从触发按钮获取数据
    $('#deleteMenuModal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget); // 获取触发模态框的按钮
        const menuId = button.data('menu-id');
        const menuName = button.data('menu-name');
        
        $('#menuNameToDelete').text(menuName);
        $('#delete_menu_id').val(menuId);
        $('#delete-menu-error').addClass('d-none');
    });
    
    // 确认删除按钮点击事件
    $('#confirmDelete').on('click', function() {
        const menuId = $('#delete_menu_id').val();
        
        if (!menuId) {
            $('#delete-error-message').text('菜单ID无效');
            $('#delete-menu-error').removeClass('d-none');
            return;
        }
        
        // 禁用按钮
        const $btn = $(this);
        $btn.prop('disabled', true);
        
        // 发送删除请求
        $.ajax({
            url: `/admin/frontend/menu/delete/${menuId}/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            },
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            dataType: 'json',
            success: function(response) {
                if (response.status === 'success') {
                    // 关闭删除确认模态框
                    $('#deleteMenuModal').modal('hide');
                    
                    // 显示成功提示
                    $('#successMessage').text(response.message || '前台菜单已删除');
                    $('#successModal').modal('show');
                    
                    // 成功模态框关闭后刷新页面
                    $('#successModal').on('hidden.bs.modal', function() {
                        window.location.reload();
                    });
                } else {
                    // 显示错误消息
                    $('#delete-error-message').text(response.message || '删除失败，请重试');
                    $('#delete-menu-error').removeClass('d-none');
                }
            },
            error: function(xhr, status, error) {
                console.error('删除菜单失败:', error);
                let errorMsg = '服务器错误，请重试';
                try {
                    const response = JSON.parse(xhr.responseText);
                    errorMsg = response.message || errorMsg;
                } catch(e) {}
                
                $('#delete-error-message').text(errorMsg);
                $('#delete-menu-error').removeClass('d-none');
            },
            complete: function() {
                // 恢复按钮状态
                $btn.prop('disabled', false);
            }
        });
    });
}

/**
 * 初始化菜单排序功能
 */
function initMenuSorting() {
    // 菜单排序
    const menuList = document.querySelector('.menu-list');
    if (menuList) {
        // 顶级菜单排序
        document.querySelectorAll('.menu-list > .menu-item-card').forEach(function(el) {
            new Sortable(menuList, {
                handle: '.drag-handle',
                animation: 150,
                onEnd: function() {
                    const menuOrder = [];
                    document.querySelectorAll('.menu-list > .menu-item-card').forEach(function(card, index) {
                        menuOrder.push({
                            id: card.dataset.id,
                            parent: null,
                            order: index
                        });
                    });
                    saveMenuOrder(menuOrder);
                }
            });
        });
        
        // 子菜单排序
        document.querySelectorAll('.submenu').forEach(function(el) {
            new Sortable(el, {
                handle: '.drag-handle',
                animation: 150,
                onEnd: function() {
                    const menuOrder = [];
                    const parentId = el.closest('.menu-item-card').dataset.id;
                    el.querySelectorAll('.menu-item-card').forEach(function(card, index) {
                        menuOrder.push({
                            id: card.dataset.id,
                            parent: parentId,
                            order: index
                        });
                    });
                    saveMenuOrder(menuOrder);
                }
            });
        });
    }
    
    // 保存菜单排序按钮点击事件
    $('#save-order').on('click', function() {
        const menuOrder = [];
        // 顶级菜单
        $('.menu-list > .menu-item-card').each(function(index) {
            menuOrder.push({
                id: $(this).data('id'),
                parent: null,
                order: index
            });
            
            // 子菜单
            $(this).find('.submenu > .menu-item-card').each(function(subIndex) {
                menuOrder.push({
                    id: $(this).data('id'),
                    parent: $(this).closest('.menu-list > .menu-item-card').data('id'),
                    order: subIndex
                });
            });
        });
        
        saveMenuOrder(menuOrder);
    });
    
    // 重置排序按钮点击事件
    $('#reset-order').on('click', function() {
        if (confirm('确定要重置菜单排序吗？')) {
            window.location.reload();
        }
    });
    
    // 保存菜单排序
    function saveMenuOrder(menuOrder) {
        if (menuOrder.length > 0) {
            // 发送排序请求
            $.ajax({
                url: '/admin/frontend/menu/save-order/',
                type: 'POST',
                data: {
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val(),
                    'menu_data': JSON.stringify(menuOrder)
                },
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                dataType: 'json',
                success: function(response) {
                    if (response.status === 'success') {
                        // 显示成功提示
                        showToast('菜单排序已更新', 'success');
                    } else {
                        showToast(response.message || '更新菜单排序失败', 'error');
                    }
                },
                error: function(xhr, status, error) {
                    showToast('更新菜单排序请求失败', 'error');
                    console.error('更新菜单排序请求失败:', error);
                }
            });
        }
    }
}

// 显示简单的通知提示
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || (() => {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    })();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * 显示表单警告信息
 * @param {jQuery} $alertsContainer - 警告容器元素
 * @param {string} type - 警告类型 (success, danger, warning, info)
 * @param {string} message - 警告消息内容
 */
function showFormAlert($alertsContainer, type, message) {
    $alertsContainer.empty();
    
    const icon = type === 'success' ? 'fa-check-circle' :
                 type === 'danger' ? 'fa-exclamation-circle' :
                 type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
    
    const alert = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas ${icon} me-2"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    $alertsContainer.append(alert);
} 