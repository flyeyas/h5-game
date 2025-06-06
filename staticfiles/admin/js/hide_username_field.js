document.addEventListener('DOMContentLoaded', function() {
    // 检查当前URL是否包含密码修改页面的路径
    if (window.location.pathname.includes('/admin/auth/user/') && window.location.pathname.includes('/password/')) {
        // 找到所有值为"testuser2"的输入框并隐藏它们
        const inputs = document.querySelectorAll('input[type="text"]');
        inputs.forEach(function(input) {
            if (input.value === 'testuser2') {
                input.style.display = 'none';
            }
        });
    }
}); 