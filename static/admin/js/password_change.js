// 密码修改页面的交互逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 获取密码认证选项
    const enabledRadio = document.getElementById('id_password_enabled_1');
    const disabledRadio = document.getElementById('id_password_enabled_0');
    const passwordFields = document.querySelectorAll('.field-password1, .field-password2');
    const submitButton = document.querySelector('.submit-row input[type="submit"]');
    
    // 密码认证选项的切换逻辑
    function togglePasswordFields() {
        if (!enabledRadio || !disabledRadio) return;
        
        const isEnabled = enabledRadio.checked;
        
        // 切换密码字段和提交按钮的状态
        passwordFields.forEach(field => {
            if (isEnabled) {
                field.style.display = 'block';
                field.style.opacity = '1';
                field.style.pointerEvents = 'auto';
            } else {
                field.style.display = 'none';
                field.style.opacity = '0.5';
                field.style.pointerEvents = 'none';
            }
        });
        
        // 更新提交按钮的文本
        if (submitButton) {
            submitButton.value = isEnabled 
                ? 'Change password' 
                : 'Disable password authentication';
        }
    }
    
    // 绑定事件监听器
    if (enabledRadio && disabledRadio) {
        enabledRadio.addEventListener('change', togglePasswordFields);
        disabledRadio.addEventListener('change', togglePasswordFields);
        
        // 初始化状态
        togglePasswordFields();
    }
    
    // 密码强度检查
    const passwordInput = document.querySelector('input[type="password"]');
    if (passwordInput) {
        const strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'password-strength';
        strengthIndicator.innerHTML = `
            <div class="strength-meter">
                <div class="strength-meter-fill"></div>
            </div>
            <span class="strength-text">Password strength: Please enter a password</span>
        `;
        
        // 将强度指示器添加到密码字段后
        passwordInput.parentNode.insertBefore(strengthIndicator, passwordInput.nextSibling);
        
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            updateStrengthIndicator(strength);
        });
    }
    
    // 检查密码强度
    function checkPasswordStrength(password) {
        if (!password) return 0;
        
        let strength = 0;
        
        // 长度检查
        if (password.length >= 8) strength += 1;
        if (password.length >= 12) strength += 1;
        
        // 包含数字
        if (/\d/.test(password)) strength += 1;
        
        // 包含小写字母
        if (/[a-z]/.test(password)) strength += 1;
        
        // 包含大写字母
        if (/[A-Z]/.test(password)) strength += 1;
        
        // 包含特殊字符
        if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
        
        return Math.min(strength, 5);
    }
    
    // 更新强度指示器
    function updateStrengthIndicator(strength) {
        const strengthIndicator = document.querySelector('.password-strength');
        if (!strengthIndicator) return;
        
        const fill = strengthIndicator.querySelector('.strength-meter-fill');
        const text = strengthIndicator.querySelector('.strength-text');
        
        // 设置填充宽度
        const fillPercentage = (strength / 5) * 100;
        fill.style.width = `${fillPercentage}%`;
        
        // 设置颜色
        let color = '#e74c3c'; // 红色 - 非常弱
        if (strength >= 2) color = '#e67e22'; // 橙色 - 弱
        if (strength >= 3) color = '#f1c40f'; // 黄色 - 中等
        if (strength >= 4) color = '#2ecc71'; // 绿色 - 强
        if (strength >= 5) color = '#27ae60'; // 深绿色 - 非常强
        
        fill.style.backgroundColor = color;
        
        // 设置文本
        const strengthTexts = [
            'Very Weak',
            'Weak',
            'Medium',
            'Strong',
            'Very Strong',
            'Excellent'
        ];
        
        text.textContent = `Password strength: ${strengthTexts[strength]}`;
    }
    
    // 添加动画效果
    const formRows = document.querySelectorAll('.form-row');
    formRows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(20px)';
        row.style.transition = 'all 0.3s ease';
        
        setTimeout(() => {
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, 100 * (index + 1));
    });
});