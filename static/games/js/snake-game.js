// 贪吃蛇游戏 JavaScript 实现
class SnakeGame {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // 游戏设置
        this.gridSize = options.gridSize || 20;
        this.tileCount = options.tileCount || 20;
        this.speed = options.speed || 7;
        
        // 初始化游戏状态
        this.snake = [{x: 10, y: 10}]; // 蛇的初始位置
        this.food = this.generateFood();
        this.direction = 'right';
        this.nextDirection = 'right';
        this.score = 0;
        this.gameOver = false;
        this.paused = false;
        
        // 绑定键盘事件
        this.bindKeyEvents();
        
        // 设置游戏循环
        this.gameLoop = null;
    }
    
    // 生成食物
    generateFood() {
        let x, y;
        let validPosition = false;
        
        while (!validPosition) {
            x = Math.floor(Math.random() * this.tileCount);
            y = Math.floor(Math.random() * this.tileCount);
            
            // 确保食物不会生成在蛇身上
            validPosition = true;
            for (let segment of this.snake) {
                if (segment.x === x && segment.y === y) {
                    validPosition = false;
                    break;
                }
            }
        }
        
        return {x, y};
    }
    
    // 绑定键盘事件
    bindKeyEvents() {
        document.addEventListener('keydown', (e) => {
            // 防止方向键滚动页面
            if(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
                e.preventDefault();
            }
            
            // 处理方向键
            switch (e.code) {
                case 'ArrowUp':
                    if (this.direction !== 'down') this.nextDirection = 'up';
                    break;
                case 'ArrowDown':
                    if (this.direction !== 'up') this.nextDirection = 'down';
                    break;
                case 'ArrowLeft':
                    if (this.direction !== 'right') this.nextDirection = 'left';
                    break;
                case 'ArrowRight':
                    if (this.direction !== 'left') this.nextDirection = 'right';
                    break;
                case 'Space':
                    this.togglePause();
                    break;
                case 'Enter':
                    if (this.gameOver) this.restart();
                    break;
            }
        });
        
        // 为移动设备添加触摸控制
        if ('ontouchstart' in window) {
            let touchStartX = 0;
            let touchStartY = 0;
            
            this.canvas.addEventListener('touchstart', (e) => {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
                e.preventDefault();
            }, false);
            
            this.canvas.addEventListener('touchmove', (e) => {
                e.preventDefault();
            }, false);
            
            this.canvas.addEventListener('touchend', (e) => {
                let touchEndX = e.changedTouches[0].clientX;
                let touchEndY = e.changedTouches[0].clientY;
                
                let dx = touchEndX - touchStartX;
                let dy = touchEndY - touchStartY;
                
                // 确定滑动方向
                if (Math.abs(dx) > Math.abs(dy)) {
                    // 水平滑动
                    if (dx > 0 && this.direction !== 'left') {
                        this.nextDirection = 'right';
                    } else if (dx < 0 && this.direction !== 'right') {
                        this.nextDirection = 'left';
                    }
                } else {
                    // 垂直滑动
                    if (dy > 0 && this.direction !== 'up') {
                        this.nextDirection = 'down';
                    } else if (dy < 0 && this.direction !== 'down') {
                        this.nextDirection = 'up';
                    }
                }
                
                e.preventDefault();
            }, false);
        }
    }
    
    // 更新游戏状态
    update() {
        if (this.gameOver || this.paused) return;
        
        // 更新方向
        this.direction = this.nextDirection;
        
        // 移动蛇
        let head = {x: this.snake[0].x, y: this.snake[0].y};
        
        switch (this.direction) {
            case 'up': head.y--; break;
            case 'down': head.y++; break;
            case 'left': head.x--; break;
            case 'right': head.x++; break;
        }
        
        // 检查碰撞
        if (this.checkCollision(head)) {
            this.gameOver = true;
            return;
        }
        
        // 添加新头部
        this.snake.unshift(head);
        
        // 检查是否吃到食物
        if (head.x === this.food.x && head.y === this.food.y) {
            this.score += 10;
            this.food = this.generateFood();
            
            // 如果分数是100的倍数，增加速度
            if (this.score % 100 === 0 && this.speed < 15) {
                this.speed++;
            }
        } else {
            // 如果没有吃到食物，移除尾部
            this.snake.pop();
        }
    }
    
    // 检查碰撞
    checkCollision(head) {
        // 检查墙壁碰撞
        if (head.x < 0 || head.x >= this.tileCount || head.y < 0 || head.y >= this.tileCount) {
            return true;
        }
        
        // 检查自身碰撞
        for (let i = 0; i < this.snake.length; i++) {
            if (this.snake[i].x === head.x && this.snake[i].y === head.y) {
                return true;
            }
        }
        
        return false;
    }
    
    // 绘制游戏
    draw() {
        // 清空画布
        this.ctx.fillStyle = '#f0f0f0';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制网格线
        this.ctx.strokeStyle = '#e0e0e0';
        this.ctx.lineWidth = 0.5;
        
        for (let i = 0; i <= this.tileCount; i++) {
            this.ctx.beginPath();
            this.ctx.moveTo(i * this.gridSize, 0);
            this.ctx.lineTo(i * this.gridSize, this.canvas.height);
            this.ctx.stroke();
            
            this.ctx.beginPath();
            this.ctx.moveTo(0, i * this.gridSize);
            this.ctx.lineTo(this.canvas.width, i * this.gridSize);
            this.ctx.stroke();
        }
        
        // 绘制食物
        this.ctx.fillStyle = '#ff0000';
        this.ctx.fillRect(
            this.food.x * this.gridSize,
            this.food.y * this.gridSize,
            this.gridSize - 2,
            this.gridSize - 2
        );
        
        // 绘制蛇
        for (let i = 0; i < this.snake.length; i++) {
            // 蛇头用不同颜色
            if (i === 0) {
                this.ctx.fillStyle = '#006400';
            } else {
                this.ctx.fillStyle = '#00aa00';
            }
            
            this.ctx.fillRect(
                this.snake[i].x * this.gridSize,
                this.snake[i].y * this.gridSize,
                this.gridSize - 2,
                this.gridSize - 2
            );
        }
        
        // 绘制分数
        this.ctx.fillStyle = '#000';
        this.ctx.font = '20px Arial';
        this.ctx.fillText(`分数: ${this.score}`, 10, 30);
        
        // 如果游戏结束，显示结束信息
        if (this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#fff';
            this.ctx.font = '30px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('游戏结束!', this.canvas.width / 2, this.canvas.height / 2 - 30);
            this.ctx.fillText(`最终分数: ${this.score}`, this.canvas.width / 2, this.canvas.height / 2 + 10);
            this.ctx.font = '20px Arial';
            this.ctx.fillText('按回车键重新开始', this.canvas.width / 2, this.canvas.height / 2 + 50);
        }
        
        // 如果游戏暂停，显示暂停信息
        if (this.paused && !this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#fff';
            this.ctx.font = '30px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('游戏暂停', this.canvas.width / 2, this.canvas.height / 2);
            this.ctx.font = '20px Arial';
            this.ctx.fillText('按空格键继续', this.canvas.width / 2, this.canvas.height / 2 + 40);
        }
    }
    
    // 游戏主循环
    run() {
        this.update();
        this.draw();
        
        if (!this.gameOver) {
            setTimeout(() => {
                requestAnimationFrame(() => this.run());
            }, 1000 / this.speed);
        } else {
            // 游戏结束，记录分数
            this.saveScore();
        }
    }
    
    // 开始游戏
    start() {
        if (!this.gameLoop) {
            this.run();
        }
    }
    
    // 暂停/继续游戏
    togglePause() {
        this.paused = !this.paused;
        if (!this.paused) {
            this.run();
        }
    }
    
    // 重新开始游戏
    restart() {
        this.snake = [{x: 10, y: 10}];
        this.food = this.generateFood();
        this.direction = 'right';
        this.nextDirection = 'right';
        this.score = 0;
        this.gameOver = false;
        this.paused = false;
        this.speed = 7;
        this.start();
    }
    
    // 保存分数
    saveScore() {
        // 如果用户已登录，可以将分数保存到服务器
        if (typeof saveGameScore === 'function') {
            saveGameScore('snake', this.score);
        }
    }
}

// 当页面加载完成时初始化游戏
document.addEventListener('DOMContentLoaded', function() {
    // 检查canvas元素是否存在
    const canvas = document.getElementById('snake-game');
    if (canvas) {
        // 设置canvas大小
        canvas.width = 400;
        canvas.height = 400;
        
        // 创建游戏实例
        const game = new SnakeGame('snake-game', {
            gridSize: 20,
            tileCount: 20,
            speed: 7
        });
        
        // 开始游戏
        game.start();
        
        // 添加开始/重新开始按钮事件
        const startButton = document.getElementById('start-game');
        if (startButton) {
            startButton.addEventListener('click', function() {
                game.restart();
            });
        }
        
        // 添加暂停/继续按钮事件
        const pauseButton = document.getElementById('pause-game');
        if (pauseButton) {
            pauseButton.addEventListener('click', function() {
                game.togglePause();
                this.textContent = game.paused ? '继续' : '暂停';
            });
        }
    }
});

// 保存游戏分数的函数
function saveGameScore(gameType, score) {
    // 获取CSRF令牌
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // 发送分数到服务器
    fetch('/games/save-score/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            game_type: gameType,
            score: score
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Score saved:', data);
    })
    .catch(error => {
        console.error('Error saving score:', error);
    });
} 