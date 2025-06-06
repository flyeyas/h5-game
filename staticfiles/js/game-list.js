/**
 * 游戏列表页面交互增强脚本
 * 提供无限滚动加载、过滤和排序功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化变量
    let currentPage = 1;
    let isLoading = false;
    let hasMorePages = document.querySelector('.pagination') !== null;
    const gamesList = document.getElementById('gamesList');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const sortDropdown = document.getElementById('sortDropdown');
    
    // 如果没有游戏列表，则不执行后续代码
    if (!gamesList) return;
    
    // 无限滚动加载功能
    function loadMoreGames() {
        if (isLoading || !hasMorePages) return;
        
        isLoading = true;
        loadingSpinner.classList.add('active');
        
        // 获取当前URL参数
        const urlParams = new URLSearchParams(window.location.search);
        const searchQuery = urlParams.get('q') || '';
        const sort = urlParams.get('sort') || 'latest';
        
        // 构建API请求URL
        currentPage++;
        let apiUrl = `?page=${currentPage}`;
        if (searchQuery) apiUrl += `&q=${searchQuery}`;
        if (sort) apiUrl += `&sort=${sort}`;
        apiUrl += '&format=json';
        
        // 发送AJAX请求
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                if (data.games && data.games.length > 0) {
                    // 添加新游戏到列表
                    renderGames(data.games);
                    hasMorePages = data.has_next;
                } else {
                    hasMorePages = false;
                }
            })
            .catch(error => {
                console.error('加载更多游戏时出错:', error);
            })
            .finally(() => {
                isLoading = false;
                loadingSpinner.classList.remove('active');
            });
    }
    
    // 渲染游戏卡片
    function renderGames(games) {
        games.forEach(game => {
            const gameCard = document.createElement('div');
            gameCard.className = 'col-lg-4 col-md-6 col-sm-6 mb-4';
            
            // 构建游戏卡片HTML
            const thumbnailUrl = game.thumbnail || '/static/img/game-placeholder.jpg';
            const stars = generateStars(game.rating);
            const categories = game.categories.slice(0, 2).map(cat => 
                `<a href="/category/${cat.slug}/" class="badge bg-secondary text-decoration-none me-1">${cat.name}</a>`
            ).join('');
            
            gameCard.innerHTML = `
                <div class="card game-card" itemscope itemtype="http://schema.org/Game">
                    <a href="/game/${game.slug}/" class="text-decoration-none">
                        <img src="${thumbnailUrl}" class="card-img-top" alt="${game.title}" itemprop="image" loading="lazy">
                    </a>
                    <div class="card-body">
                        <h5 class="card-title" itemprop="name">
                            <a href="/game/${game.slug}/" class="text-decoration-none text-dark" itemprop="url">${game.title}</a>
                        </h5>
                        <p class="card-text small" itemprop="description">${game.description}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="small text-warning">${stars}</div>
                            <small class="text-muted"><i class="fas fa-eye me-1"></i> ${game.view_count} views</small>
                        </div>
                        <div class="mt-2">${categories}</div>
                    </div>
                    <div class="card-footer bg-transparent border-top-0">
                        <a href="/game/${game.slug}/" class="btn btn-sm btn-primary w-100">Play Game</a>
                    </div>
                </div>
            `;
            
            gamesList.appendChild(gameCard);
        });
    }
    
    // 生成星级评分HTML
    function generateStars(rating) {
        let starsHtml = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                starsHtml += '<i class="fas fa-star"></i>';
            } else {
                starsHtml += '<i class="far fa-star"></i>';
            }
        }
        return starsHtml;
    }
    
    // 监听滚动事件，实现无限滚动
    window.addEventListener('scroll', function() {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
            loadMoreGames();
        }
    });
    
    // 排序功能
    if (sortDropdown) {
        const sortLinks = document.querySelectorAll('.dropdown-menu .dropdown-item');
        sortLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.href = this.getAttribute('href');
            });
        });
    }
    
    // 游戏卡片悬停效果
    const gameCards = document.querySelectorAll('.game-card');
    gameCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });
});