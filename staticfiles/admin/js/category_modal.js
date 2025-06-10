// category_modal.js - 处理分类添加和编辑模态框功能

document.addEventListener('DOMContentLoaded', function() {
    // 表单验证
    const categoryForm = document.getElementById('addCategoryForm');
    if (categoryForm) {
        categoryForm.addEventListener('submit', function(event) {
            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    }

    // 编辑分类表单验证
    const editCategoryForm = document.getElementById('editCategoryForm');
    if (editCategoryForm) {
        editCategoryForm.addEventListener('submit', function(event) {
            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    }

    // 保存分类按钮点击事件
    const saveCategoryBtn = document.getElementById('saveCategoryBtn');
    if (saveCategoryBtn) {
        saveCategoryBtn.addEventListener('click', function() {
            const form = document.getElementById('addCategoryForm');

            // 手动触发表单验证
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                return;
            }

            // 使用AJAX提交表单
            const formData = new FormData(form);

            // 获取CSRF令牌
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // 修复URL路径问题，确保始终使用完整的URL路径
            const baseUrl = window.location.pathname.includes('/en/') ? '/en' : '/zh';
            const apiUrl = `${baseUrl}/api/category/add/`;

            // 禁用按钮，防止重复提交
            saveCategoryBtn.disabled = true;
            saveCategoryBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';

            fetch(apiUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // 显示成功消息
                    showToast('success', data.message || 'Category added successfully');

                    // 关闭模态框
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addCategoryModal'));
                    modal.hide();

                    // 重置表单
                    form.reset();
                    form.classList.remove('was-validated');

                    // 刷新页面以显示新添加的分类
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    // 显示错误消息
                    showToast('danger', data.message || 'Failed to add category');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('danger', 'An error occurred while processing your request: ' + error.message);
            })
            .finally(() => {
                // 恢复按钮状态
                saveCategoryBtn.disabled = false;
                saveCategoryBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save category';
            });
        });
    }

    // 更新分类按钮点击事件
    const updateCategoryBtn = document.getElementById('updateCategoryBtn');
    if (updateCategoryBtn) {
        updateCategoryBtn.addEventListener('click', function() {
            const form = document.getElementById('editCategoryForm');
            
            // 手动触发表单验证
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                return;
            }
            
            // 使用Fetch API提交表单
            const formData = new FormData(form);
            const categoryId = form.dataset.categoryId;
            document.getElementById('edit_category_id').value = categoryId;

            // 获取CSRF令牌
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // 修复URL路径问题，确保始终使用完整的URL路径
            const baseUrl = window.location.pathname.includes('/en/') ? '/en' : '/zh';
            const apiUrl = `${baseUrl}/api/category/${categoryId}/edit/`;

            // 禁用按钮，防止重复提交
            updateCategoryBtn.disabled = true;
            updateCategoryBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Updating...';

            fetch(apiUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // 显示成功消息
                    showToast('success', data.message || 'Category updated successfully');

                    // 关闭模态框
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editCategoryModal'));
                    modal.hide();

                    // 刷新页面以显示更新后的分类
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    // 显示错误消息
                    showToast('danger', data.message || 'Failed to update category');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('danger', 'An error occurred while processing your request: ' + error.message);
            })
            .finally(() => {
                // 恢复按钮状态
                updateCategoryBtn.disabled = false;
                updateCategoryBtn.innerHTML = '<i class="fas fa-save me-2"></i>Update category';
            });
        });
    }

    // Slug字段已移除，无需相关JavaScript处理
    // 分类的slug将由后端自动生成唯一哈希串

    // 处理编辑按钮点击事件
    document.querySelectorAll('.edit-category-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const categoryId = this.dataset.categoryId;
            loadCategoryData(categoryId);
        });
    });

    // 处理查看按钮点击事件
    document.querySelectorAll('.view-category-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const categoryId = this.dataset.categoryId;
            loadCategoryDetails(categoryId);
        });
    });

    // 处理删除按钮点击事件
    document.querySelectorAll('.delete-category-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const categoryId = this.dataset.categoryId;
            const categoryName = this.dataset.categoryName;
            
            // 设置确认对话框中的分类名称
            document.getElementById('delete_category_name').textContent = categoryName;
            
            // 设置确认按钮的分类ID
            document.getElementById('confirmDeleteBtn').dataset.categoryId = categoryId;
            
            // 隐藏警告信息
            const warningsContainer = document.getElementById('delete_category_warnings');
            warningsContainer.classList.add('d-none');
            warningsContainer.innerHTML = '';
            
            // 显示确认对话框
            const modal = new bootstrap.Modal(document.getElementById('deleteCategoryModal'));
            modal.show();
        });
    });

    // 处理确认删除按钮点击事件
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            const categoryId = this.dataset.categoryId;
            deleteCategory(categoryId);
        });
    }

    // 查看详情模态框中的编辑按钮点击事件
    const viewEditBtn = document.querySelector('.view-edit-btn');
    if (viewEditBtn) {
        viewEditBtn.addEventListener('click', function() {
            // 获取当前查看的分类ID
            const categoryId = this.dataset.categoryId;
            
            // 关闭查看模态框
            const viewModal = bootstrap.Modal.getInstance(document.getElementById('viewCategoryModal'));
            viewModal.hide();
            
            // 打开编辑模态框
            loadCategoryData(categoryId);
        });
    }

    // 加载分类数据
    function loadCategoryData(categoryId) {
        // 修复URL路径问题，确保始终使用完整的URL路径
        const baseUrl = window.location.pathname.includes('/en/') ? '/en' : '/zh';
        const apiUrl = `${baseUrl}/api/category/${categoryId}/json/`;
        
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                // 设置表单数据
                const form = document.getElementById('editCategoryForm');
                if (form) {
                    form.dataset.categoryId = categoryId;
                }

                const editCategoryIdEl = document.getElementById('edit_category_id');
                if (editCategoryIdEl) {
                    editCategoryIdEl.value = categoryId;
                }

                const editNameEl = document.getElementById('edit_name');
                if (editNameEl) {
                    editNameEl.value = data.name;
                }

                const editSlugEl = document.getElementById('edit_slug');
                if (editSlugEl) {
                    editSlugEl.value = data.slug;
                }

                const editDescriptionEl = document.getElementById('edit_description');
                if (editDescriptionEl) {
                    editDescriptionEl.value = data.description || '';
                }

                const editIconClassEl = document.getElementById('edit_icon_class');
                if (editIconClassEl) {
                    editIconClassEl.value = data.icon_class || '';
                }

                // 设置父级分类
                const parentSelect = document.getElementById('edit_parent');
                if (parentSelect) {
                    // 重置选项
                    for (let i = 0; i < parentSelect.options.length; i++) {
                        if (parentSelect.options[i].value == data.parent_id) {
                            parentSelect.options[i].selected = true;
                            break;
                        }
                    }
                }

                // 设置活动状态
                const editIsActiveEl = document.getElementById('edit_is_active');
                if (editIsActiveEl) {
                    editIsActiveEl.checked = data.is_active;
                }

                // 显示模态框
                const editModal = document.getElementById('editCategoryModal');
                if (editModal) {
                    const modal = new bootstrap.Modal(editModal);
                    modal.show();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('danger', '加载分类数据时发生错误: ' + error.message);
            });
    }

    // 加载分类详情
    function loadCategoryDetails(categoryId) {
        // 修复URL路径问题，确保始终使用完整的URL路径
        const baseUrl = window.location.pathname.includes('/en/') ? '/en' : '/zh';
        const apiUrl = `${baseUrl}/api/category/${categoryId}/view/`;
        
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                // 设置基本信息
                const viewNameEl = document.getElementById('view_name');
                if (viewNameEl) {
                    viewNameEl.textContent = data.name;
                }

                const viewSlugEl = document.getElementById('view_slug');
                if (viewSlugEl) {
                    viewSlugEl.textContent = data.slug;
                }

                const viewParentEl = document.getElementById('view_parent');
                if (viewParentEl) {
                    viewParentEl.textContent = data.parent || '-';
                }

                // 设置状态
                const statusElement = document.getElementById('view_status');
                if (statusElement) {
                    if (data.is_active) {
                        statusElement.innerHTML = '<span class="badge bg-success">Active</span>';
                    } else {
                        statusElement.innerHTML = '<span class="badge bg-secondary">Inactive</span>';
                    }
                }

                // 设置游戏数量
                const viewGameCountEl = document.getElementById('view_game_count');
                if (viewGameCountEl) {
                    viewGameCountEl.textContent = data.game_count;
                }

                // 设置时间戳
                const viewCreatedAtEl = document.getElementById('view_created_at');
                if (viewCreatedAtEl) {
                    viewCreatedAtEl.textContent = data.created_at;
                }

                const viewUpdatedAtEl = document.getElementById('view_updated_at');
                if (viewUpdatedAtEl) {
                    viewUpdatedAtEl.textContent = data.updated_at;
                }

                // 设置描述
                const viewDescriptionEl = document.getElementById('view_description');
                if (viewDescriptionEl) {
                    viewDescriptionEl.textContent = data.description || '(No description)';
                }

                // 设置图标
                const iconElement = document.getElementById('view_icon');
                if (iconElement) {
                    if (data.icon_class) {
                        iconElement.innerHTML = `<i class="${data.icon_class}"></i> ${data.icon_class}`;
                    } else {
                        iconElement.textContent = '(No icon)';
                    }
                }

                // 设置图片
                const imageElement = document.getElementById('view_image');
                if (imageElement) {
                    if (data.image_url) {
                        imageElement.src = data.image_url;
                        imageElement.classList.remove('d-none');
                    } else {
                        imageElement.classList.add('d-none');
                    }
                }
                
                // 设置游戏列表
                const gamesList = document.getElementById('view_games_list');
                const gamesTable = document.getElementById('view_games_table');
                const noGamesAlert = document.getElementById('view_no_games');
                
                // 清空现有游戏列表
                gamesList.innerHTML = '';
                
                if (data.games && data.games.length > 0) {
                    // 有游戏时显示表格，隐藏提示
                    gamesTable.classList.remove('d-none');
                    noGamesAlert.classList.add('d-none');
                    
                    // 添加游戏到列表
                    data.games.forEach((game, index) => {
                        const row = document.createElement('tr');
                        
                        // 设置行内容
                        row.innerHTML = `
                            <td>${index + 1}</td>
                            <td>${game.title}</td>
                            <td>${game.is_active ? 
                                '<span class="badge bg-success">Active</span>' : 
                                '<span class="badge bg-secondary">Inactive</span>'}</td>
                            <td>
                                <a href="${baseUrl}/admin/games/game/${game.id}/change/" 
                                   class="btn btn-sm btn-outline-primary" target="_blank">
                                    <i class="fas fa-edit"></i>
                                </a>
                                <a href="${baseUrl}/game/${game.slug}/" 
                                   class="btn btn-sm btn-outline-info" target="_blank">
                                    <i class="fas fa-external-link-alt"></i>
                                </a>
                            </td>
                        `;
                        
                        gamesList.appendChild(row);
                    });
                } else {
                    // 没有游戏时隐藏表格，显示提示
                    gamesTable.classList.add('d-none');
                    noGamesAlert.classList.remove('d-none');
                }
                
                // 为编辑按钮存储分类ID
                document.querySelector('.view-edit-btn').dataset.categoryId = categoryId;
                
                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('viewCategoryModal'));
                modal.show();
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('danger', '加载分类详情时发生错误: ' + error.message);
            });
    }

    // 删除分类
    function deleteCategory(categoryId) {
        // 获取确认删除按钮
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

        // 获取CSRF令牌
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // 修复URL路径问题，确保始终使用完整的URL路径
        const baseUrl = window.location.pathname.includes('/en/') ? '/en' : '/zh';
        const apiUrl = `${baseUrl}/api/category/${categoryId}/delete/`;

        // 禁用按钮，防止重复提交
        confirmDeleteBtn.disabled = true;
        confirmDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';

        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            // 先获取JSON响应
            return response.json().then(data => {
                // 将状态码和数据一起返回
                return { status: response.status, data };
            });
        })
        .then(result => {
            const { status, data } = result;
            
            if (status === 200 && data.success) {
                // 显示成功消息
                showToast('success', data.message || 'Category deleted successfully');

                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteCategoryModal'));
                modal.hide();

                // 刷新页面以更新分类列表
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                // 显示错误消息
                if (status === 400) {
                    // 显示具体的验证错误
                    const warningsContainer = document.getElementById('delete_category_warnings');
                    warningsContainer.innerHTML = data.message;
                    warningsContainer.classList.remove('d-none');

                    // 如果是游戏关联错误，添加游戏计数
                    if (data.game_count) {
                        warningsContainer.innerHTML += `<div class="mt-2">Associated games: ${data.game_count}</div>`;
                    }

                    // 如果是子分类关联错误，添加子分类计数
                    if (data.children_count) {
                        warningsContainer.innerHTML += `<div class="mt-2">Subcategories: ${data.children_count}</div>`;
                    }

                    // 显示警告Toast
                    showToast('warning', data.message, 'Cannot Delete Category');
                } else {
                    // 显示通用错误
                    showToast('danger', data.message || 'Failed to delete category');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('danger', 'An error occurred while processing your request: ' + error.message);
        })
        .finally(() => {
            // 恢复按钮状态
            confirmDeleteBtn.disabled = false;
            confirmDeleteBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Delete';
        });
    }

    // 显示Bootstrap Toast提示消息
    window.showToast = function(type, message, title = null, duration = 5000) {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            console.error('Toast container not found');
            return;
        }

        // 生成唯一ID
        const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

        // 根据类型设置图标和标题
        let icon, toastTitle, bgClass, textClass;
        switch (type) {
            case 'success':
                icon = 'fas fa-check-circle';
                toastTitle = title || 'Success';
                bgClass = 'bg-success';
                textClass = 'text-white';
                break;
            case 'danger':
            case 'error':
                icon = 'fas fa-exclamation-circle';
                toastTitle = title || 'Error';
                bgClass = 'bg-danger';
                textClass = 'text-white';
                break;
            case 'warning':
                icon = 'fas fa-exclamation-triangle';
                toastTitle = title || 'Warning';
                bgClass = 'bg-warning';
                textClass = 'text-dark';
                break;
            case 'info':
                icon = 'fas fa-info-circle';
                toastTitle = title || 'Information';
                bgClass = 'bg-info';
                textClass = 'text-white';
                break;
            default:
                icon = 'fas fa-bell';
                toastTitle = title || 'Notification';
                bgClass = 'bg-primary';
                textClass = 'text-white';
        }

        // 创建Toast元素
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast ${bgClass} ${textClass}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="toast-header ${bgClass} ${textClass} border-0">
                <i class="${icon} me-2"></i>
                <strong class="me-auto">${toastTitle}</strong>
                <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                <button type="button" class="btn-close ${textClass === 'text-white' ? 'btn-close-white' : ''}"
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        // 添加到容器
        toastContainer.appendChild(toast);

        // 创建Bootstrap Toast实例
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });

        // 显示Toast
        bsToast.show();

        // 监听隐藏事件，移除DOM元素
        toast.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });

        // 返回Toast实例，以便外部控制
        return bsToast;
    };
}); 