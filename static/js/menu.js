// 菜单管理JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化菜单添加表单提交处理
    initMenuFormSubmit();
    
    // 初始化菜单编辑表单提交处理
    initEditMenuForm();
    
    // 初始化删除菜单功能
    initDeleteMenu();
});

// 初始化菜单添加表单Ajax提交
function initMenuFormSubmit() {
    const menuForm = document.getElementById('menuForm');
    if (!menuForm) return;
    
    menuForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 显示加载状态
        const submitBtn = document.getElementById('submitMenuForm');
        const spinner = submitBtn.querySelector('.spinner-border');
        submitBtn.disabled = true;
        spinner.classList.remove('d-none');
        
        // 清除之前的提示
        const alertsContainer = document.getElementById('formAlerts');
        alertsContainer.innerHTML = '';
        
        // 收集表单数据
        const formData = new FormData(menuForm);
        
        // 发送Ajax请求
        fetch(menuForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // 恢复按钮状态
            submitBtn.disabled = false;
            spinner.classList.add('d-none');
            
            if (data.status === 'success') {
                // 添加成功
                // 关闭添加菜单模态框
                const addMenuModal = bootstrap.Modal.getInstance(document.getElementById('addMenuModal'));
                addMenuModal.hide();
                
                // 显示成功模态框
                showSuccessModal(data.message || '菜单添加成功', function() {
                    // 重新加载页面或者添加到DOM
                    appendMenuToDOM(data.menu);
                });
                
                // 清空表单
                menuForm.reset();
            } else {
                // 添加失败，显示错误信息
                showFormErrors(alertsContainer, data.errors || {'__all__': [data.message || '添加菜单失败']});
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitBtn.disabled = false;
            spinner.classList.add('d-none');
            
            // 显示错误信息
            showFormErrors(alertsContainer, {'__all__': ['请求处理失败，请稍后重试']});
        });
    });
}

// 初始化菜单编辑表单
function initEditMenuForm() {
    const editMenuForm = document.getElementById('editMenuForm');
    if (!editMenuForm) return;
    
    // 编辑菜单按钮点击处理
    document.querySelectorAll('.edit-menu-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const menuId = this.getAttribute('data-menu-id');
            loadMenuDetails(menuId);
        });
    });
    
    // 编辑表单提交处理
    editMenuForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const menuId = document.getElementById('edit_menu_id').value;
        if (!menuId) return;
        
        // 显示加载状态
        const submitBtn = document.getElementById('submitEditForm');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> 保存中...';
        
        // 清除之前的提示
        const alertsContainer = document.getElementById('editFormAlerts');
        alertsContainer.innerHTML = '';
        
        // 收集表单数据
        const formData = new FormData(editMenuForm);
        
        // 发送Ajax请求
        fetch(`/admin/menus/edit/${menuId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // 恢复按钮状态
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> 保存修改';
            
            if (data.status === 'success') {
                // 编辑成功
                // 关闭编辑菜单模态框
                const editMenuModal = bootstrap.Modal.getInstance(document.getElementById('editMenuModal'));
                editMenuModal.hide();
                
                // 显示成功模态框
                showSuccessModal(data.message || '菜单修改成功', function() {
                    // 重新加载页面或者更新DOM
                    window.location.reload();
                });
            } else {
                // 编辑失败，显示错误信息
                showFormErrors(alertsContainer, data.errors || {'__all__': [data.message || '修改菜单失败']});
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> 保存修改';
            
            // 显示错误信息
            showFormErrors(alertsContainer, {'__all__': ['请求处理失败，请稍后重试']});
        });
    });
}

// 加载菜单详情
function loadMenuDetails(menuId) {
    // 显示加载状态
    document.getElementById('editFormLoading').style.display = 'block';
    document.getElementById('editFormContent').style.display = 'none';
    
    // 发送请求获取菜单详情
    fetch(`/admin/menu/${menuId}/get/`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            fillEditForm(data.menu);
        } else {
            alert(data.message || '获取菜单信息失败');
            const editMenuModal = bootstrap.Modal.getInstance(document.getElementById('editMenuModal'));
            editMenuModal.hide();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('请求处理失败，请稍后重试');
        const editMenuModal = bootstrap.Modal.getInstance(document.getElementById('editMenuModal'));
        editMenuModal.hide();
    })
    .finally(() => {
        // 隐藏加载状态
        document.getElementById('editFormLoading').style.display = 'none';
        document.getElementById('editFormContent').style.display = 'block';
    });
}

// 填充编辑表单
function fillEditForm(menu) {
    document.getElementById('edit_menu_id').value = menu.id;
    document.getElementById('edit_name').value = menu.name || '';
    document.getElementById('edit_url').value = menu.url || '';
    document.getElementById('edit_icon').value = menu.icon || '';
    document.getElementById('edit_order').value = menu.order || 0;
    document.getElementById('edit_is_active').checked = menu.is_active;
    
    // 更新图标预览
    if (menu.icon) {
        document.getElementById('edit_icon_preview').className = menu.icon;
    } else {
        document.getElementById('edit_icon_preview').className = 'fas fa-gear';
    }
    
    // 设置父级菜单
    const parentSelect = document.getElementById('edit_parent');
    if (parentSelect) {
        for (let i = 0; i < parentSelect.options.length; i++) {
            if (menu.parent && parentSelect.options[i].value == menu.parent) {
                parentSelect.selectedIndex = i;
                break;
            } else if (!menu.parent && parentSelect.options[i].value === '') {
                parentSelect.selectedIndex = i;
                break;
            }
        }
    }
}

// 初始化删除菜单功能
function initDeleteMenu() {
    // 删除模态框打开前处理
    document.getElementById('deleteMenuModal').addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        const menuId = button.getAttribute('data-menu-id');
        const menuName = button.getAttribute('data-menu-name');
        
        document.getElementById('menuNameToDelete').textContent = menuName;
        document.getElementById('delete_menu_id').value = menuId;
    });
    
    // 确认删除按钮点击处理
    document.getElementById('confirmDelete').addEventListener('click', function() {
        const menuId = document.getElementById('delete_menu_id').value;
        if (!menuId) return;
        
        // 禁用按钮，显示加载状态
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> 删除中...';
        
        // 发送删除请求
        fetch(`/admin/menus/delete/${menuId}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            // 恢复按钮状态
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-trash me-1"></i> 确认删除';
            
            if (data.status === 'success') {
                // 删除成功
                // 关闭删除确认模态框
                const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteMenuModal'));
                deleteModal.hide();
                
                // 显示成功模态框
                showSuccessModal(data.message || '菜单删除成功', function() {
                    // 从DOM中移除被删除的菜单项
                    removeMenuFromDOM(menuId);
                });
            } else {
                // 删除失败，显示错误信息
                document.getElementById('delete-menu-error').classList.remove('d-none');
                document.getElementById('delete-error-message').textContent = data.message || '删除失败，请重试';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-trash me-1"></i> 确认删除';
            
            // 显示错误信息
            document.getElementById('delete-menu-error').classList.remove('d-none');
            document.getElementById('delete-error-message').textContent = '请求处理失败，请稍后重试';
        });
    });
}

// 显示表单错误
function showFormErrors(container, errors) {
    container.innerHTML = '';
    
    // 通用错误
    if (errors.__all__) {
        const generalError = document.createElement('div');
        generalError.className = 'alert alert-danger';
        generalError.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${errors.__all__[0]}`;
        container.appendChild(generalError);
    }
    
    // 字段特定错误
    for (const field in errors) {
        if (field === '__all__') continue;
        
        const fieldInput = document.getElementById(`id_${field}`) || document.getElementById(`edit_${field}`);
        if (fieldInput) {
            fieldInput.classList.add('is-invalid');
            
            // 显示错误信息
            const feedback = fieldInput.nextElementSibling;
            if (feedback && feedback.classList.contains('invalid-feedback')) {
                feedback.textContent = errors[field][0];
            }
        }
    }
}

// 显示成功模态框
function showSuccessModal(message, callback) {
    const successModal = document.getElementById('successModal');
    if (!successModal) return;
    
    document.getElementById('successMessage').textContent = message;
    
    const modal = new bootstrap.Modal(successModal);
    modal.show();
    
    // 在模态框关闭后执行回调
    successModal.addEventListener('hidden.bs.modal', function handler() {
        if (typeof callback === 'function') {
            callback();
        }
        successModal.removeEventListener('hidden.bs.modal', handler);
    });
}

// 新增菜单项添加到DOM
function appendMenuToDOM(menu) {
    // 采用简单的页面刷新方式更新，避免复杂的DOM操作
    window.location.reload();
}

// 从DOM移除菜单项
function removeMenuFromDOM(menuId) {
    // 采用简单的页面刷新方式更新，避免复杂的DOM操作
    window.location.reload();
} 