document.addEventListener('DOMContentLoaded', function() {
    // 初始化游戏卡片悬停效果
    initGameCardHover();
    
    // 初始化筛选和排序功能
    initFilterAndSort();
    
    // 初始化加载更多游戏功能（如果有分页）
    initPagination();
    
    // 初始化搜索功能
    initSearch();
});

/**
 * 初始化游戏卡片悬停效果
 */
function initGameCardHover() {
    const gameCards = document.querySelectorAll('.game-card');
    
    gameCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * 初始化筛选和排序功能
 */
function initFilterAndSort() {
    // 当选择框值改变时自动提交表单
    const sortSelect = document.querySelector('select[name="sort"]');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            this.closest('form').submit();
        });
    }
}

/**
 * 初始化分页功能
 */
function initPagination() {
    // 将活动的分页项添加适当的样式
    const currentPage = document.querySelector('.pagination .active');
    if (currentPage) {
        currentPage.classList.add('fw-bold');
    }
    
    // 为分页链接添加过渡效果
    const pageLinks = document.querySelectorAll('.page-link');
    pageLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.3s ease';
            this.style.backgroundColor = '#f0f0f0';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
}

/**
 * 初始化搜索功能
 */
function initSearch() {
    const searchForm = document.querySelector('#searchForm');
    const searchInput = document.querySelector('#searchInput');
    
    if (searchForm && searchInput) {
        // 防抖动搜索，避免频繁请求
        let searchTimeout;
        
        searchInput.addEventListener('keyup', function() {
            clearTimeout(searchTimeout);
            
            // 检查搜索输入是否为空
            if (this.value.trim().length === 0) {
                return;
            }
            
            // 输入停止300ms后才执行搜索
            searchTimeout = setTimeout(() => {
                searchForm.submit();
            }, 300);
        });
    }
} 