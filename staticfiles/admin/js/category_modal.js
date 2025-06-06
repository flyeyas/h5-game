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
            
            // 提交表单
            form.submit();
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
                    showToast('success', data.message || '分类更新成功');
                    
                    // 关闭模态框
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editCategoryModal'));
                    modal.hide();
                    
                    // 刷新页面以显示更新后的分类
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    // 显示错误消息
                    showToast('danger', data.message || '分类更新失败');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('danger', '处理请求时发生错误: ' + error.message);
            });
        });
    }

    // 自动生成分类别名
    const categoryNameInput = document.getElementById('id_name');
    if (categoryNameInput) {
        categoryNameInput.addEventListener('input', function() {
            const slugInput = document.getElementById('id_slug');
            // 如果别名为空，则自动生成
            if (slugInput && !slugInput.value) {
                // 将输入转换为URL友好的格式
                const slug = this.value
                    .toLowerCase()
                    .replace(/\s+/g, '-')
                    .replace(/[^\w\-]+/g, '');
                slugInput.value = slug;
            }
        });
    }

    // 编辑分类模态框中自动生成分类别名
    const editCategoryNameInput = document.getElementById('edit_name');
    if (editCategoryNameInput) {
        editCategoryNameInput.addEventListener('input', function() {
            const slugInput = document.getElementById('edit_slug');
            // 如果别名为空，则自动生成
            if (slugInput && !slugInput.value) {
                // 将输入转换为URL友好的格式
                const slug = this.value
                    .toLowerCase()
                    .replace(/\s+/g, '-')
                    .replace(/[^\w\-]+/g, '');
                slugInput.value = slug;
            }
        });
    }

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
                form.dataset.categoryId = categoryId;
                document.getElementById('edit_category_id').value = categoryId;
                
                document.getElementById('edit_name').value = data.name;
                document.getElementById('edit_slug').value = data.slug;
                document.getElementById('edit_description').value = data.description || '';
                document.getElementById('edit_order').value = data.order || 0;
                
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
                document.getElementById('edit_is_active').checked = data.is_active;
                
                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('editCategoryModal'));
                modal.show();
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
                document.getElementById('view_name').textContent = data.name;
                document.getElementById('view_slug').textContent = data.slug;
                document.getElementById('view_parent').textContent = data.parent || '-';
                document.getElementById('view_order').textContent = data.order;
                
                // 设置状态
                const statusElement = document.getElementById('view_status');
                if (data.is_active) {
                    statusElement.innerHTML = '<span class="badge bg-success">Active</span>';
                } else {
                    statusElement.innerHTML = '<span class="badge bg-secondary">Inactive</span>';
                }
                
                // 设置游戏数量
                document.getElementById('view_game_count').textContent = data.game_count;
                
                // 设置时间戳
                document.getElementById('view_created_at').textContent = data.created_at;
                document.getElementById('view_updated_at').textContent = data.updated_at;
                
                // 设置描述
                document.getElementById('view_description').textContent = data.description || '(No description)';
                
                // 设置图标
                const iconElement = document.getElementById('view_icon');
                if (data.icon_class) {
                    iconElement.innerHTML = `<i class="${data.icon_class}"></i> ${data.icon_class}`;
                } else {
                    iconElement.textContent = '(No icon)';
                }
                
                // 设置图片
                const imageElement = document.getElementById('view_image');
                if (data.image_url) {
                    imageElement.src = data.image_url;
                    imageElement.classList.remove('d-none');
                } else {
                    imageElement.classList.add('d-none');
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
        // 获取CSRF令牌
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // 修复URL路径问题，确保始终使用完整的URL路径
        const baseUrl = window.location.pathname.includes('/en/') ? '/en' : '/zh';
        const apiUrl = `${baseUrl}/api/category/${categoryId}/delete/`;
        
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
                showToast('success', data.message || '分类删除成功');
                
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
                        warningsContainer.innerHTML += `<div class="mt-2">关联游戏数: ${data.game_count}</div>`;
                    }
                    
                    // 如果是子分类关联错误，添加子分类计数
                    if (data.children_count) {
                        warningsContainer.innerHTML += `<div class="mt-2">子分类数: ${data.children_count}</div>`;
                    }
                } else {
                    // 显示通用错误
                    showToast('danger', data.message || '分类删除失败');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('danger', '处理请求时发生错误: ' + error.message);
        });
    }

    // 显示提示消息
    window.showToast = function(type, message) {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast bg-${type} text-white`;
        toast.innerHTML = `
            <div class="toast-body">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white" onclick="this.parentElement.remove()"></button>
        `;
        
        toastContainer.appendChild(toast);
        
        // 3秒后自动移除
        setTimeout(() => {
            toast.remove();
        }, 3000);
    };
}); 