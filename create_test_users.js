// 自动化创建测试用户的脚本
async function createTestUsers() {
    // 从testuser3开始创建到testuser20（因为testuser1和testuser2已经存在）
    for (let i = 3; i <= 20; i++) {
        try {
            console.log(`Creating testuser${i}...`);
            
            // 填写用户名
            await page.getByRole('textbox', { name: 'Username:' }).fill(`testuser${i}`);
            
            // 填写密码
            await page.getByRole('textbox', { name: 'Password:' }).fill('testpass123');
            
            // 填写确认密码
            await page.getByRole('textbox', { name: 'Password confirmation:' }).fill('testpass123');
            
            // 点击保存按钮
            await page.getByRole('button', { name: 'Save' }).click();
            
            // 等待页面加载
            await page.waitForTimeout(1000);
            
            // 如果不是最后一个用户，点击"Add user"按钮继续创建
            if (i < 20) {
                await page.getByRole('button', { name: '+ Add user' }).click();
                await page.waitForTimeout(500);
            }
            
            console.log(`testuser${i} created successfully`);
            
        } catch (error) {
            console.error(`Error creating testuser${i}:`, error);
            break;
        }
    }
    
    console.log('All test users creation completed!');
}

// 执行脚本
createTestUsers();
