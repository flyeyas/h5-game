import os
import django
from django.utils.text import slugify
import random

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

from core.models import GameCategory, GameTag, Game


def slugify_with_id(name):
    """生成带随机ID的slug，避免重复"""
    base_slug = slugify(name)
    random_id = random.randint(1000, 9999)
    return f"{base_slug}-{random_id}"


def create_test_categories():
    """创建测试分类数据"""
    categories = [
        {
            'name': '动作游戏',
            'description': '激烈刺激的动作类游戏，考验玩家反应速度和操作技巧',
            'icon': 'fas fa-bolt',
            'color': '#E74C3C',
        },
        {
            'name': '休闲游戏',
            'description': '轻松有趣的休闲游戏，适合任何年龄段的玩家',
            'icon': 'fas fa-coffee',
            'color': '#3498DB',
        },
        {
            'name': '解谜游戏',
            'description': '需要思考和推理的解谜类游戏，挑战玩家的智力',
            'icon': 'fas fa-puzzle-piece',
            'color': '#9B59B6',
        },
        {
            'name': '策略游戏',
            'description': '需要战略规划的策略类游戏，培养玩家的思维能力',
            'icon': 'fas fa-chess',
            'color': '#2ECC71',
        }
    ]
    
    for i, category_data in enumerate(categories):
        try:
            # 尝试获取现有分类
            category = GameCategory.objects.get(name=category_data['name'])
            print(f"分类已存在: {category.name}")
        except GameCategory.DoesNotExist:
            # 创建新分类
            category = GameCategory.objects.create(
                name=category_data['name'],
                slug=slugify_with_id(category_data['name']),
                description=category_data['description'],
                icon=category_data['icon'],
                color=category_data['color'],
                order=i,
                is_active=True,
            )
            print(f"创建了分类: {category.name}")


def create_test_tags():
    """创建测试标签数据"""
    tags = ["多人游戏", "单人游戏", "免费游戏", "热门游戏", "新品游戏", "音乐游戏", "塔防游戏", "竞速游戏"]
    
    for tag_name in tags:
        try:
            # 尝试获取现有标签
            tag = GameTag.objects.get(name=tag_name)
            print(f"标签已存在: {tag.name}")
        except GameTag.DoesNotExist:
            # 创建新标签
            tag = GameTag.objects.create(
                name=tag_name,
                slug=slugify_with_id(tag_name),
                is_active=True,
            )
            print(f"创建了标签: {tag.name}")


def create_test_games():
    """创建测试游戏数据"""
    # 获取分类
    categories = GameCategory.objects.all()
    if not categories.exists():
        print("请先创建分类")
        return
    
    # 获取标签
    tags = GameTag.objects.all()
    if not tags.exists():
        print("请先创建标签")
        return
    
    games_data = [
        {
            'title': '太空冒险',
            'description': '在浩瀚的宇宙中展开一场惊险刺激的冒险，躲避小行星，收集能量晶体。',
            'iframe_url': 'https://example.com/games/space-adventure',
            'status': 'online',
            'is_featured': True,
            'rating': 4.5,
        },
        {
            'title': '水果忍者',
            'description': '切水果的快感！挥动手指切开各种水果，小心炸弹！',
            'iframe_url': 'https://example.com/games/fruit-ninja',
            'status': 'online',
            'is_featured': True,
            'rating': 4.7,
        },
        {
            'title': '益智方块',
            'description': '经典的方块消除游戏，挑战你的思维极限。',
            'iframe_url': 'https://example.com/games/puzzle-blocks',
            'status': 'online',
            'is_featured': False,
            'rating': 4.2,
        },
        {
            'title': '赛车狂飙',
            'description': '紧张刺激的赛车游戏，体验极速飞驰的感觉。',
            'iframe_url': 'https://example.com/games/racing-madness',
            'status': 'online',
            'is_featured': False,
            'rating': 4.0,
        },
    ]
    
    for i, game_data in enumerate(games_data):
        try:
            # 尝试获取现有游戏
            game = Game.objects.get(title=game_data['title'])
            print(f"游戏已存在: {game.title}")
        except Game.DoesNotExist:
            # 创建新游戏
            game = Game.objects.create(
                title=game_data['title'],
                slug=slugify_with_id(game_data['title']),
                description=game_data['description'],
                iframe_url=game_data['iframe_url'],
                status=game_data['status'],
                is_featured=game_data['is_featured'],
                rating=game_data['rating'],
                play_count=i * 10 + 5,  # 随机播放次数
            )
            
            # 添加分类 (每个游戏随机1-2个分类)
            category_count = min(2, categories.count())
            for category in categories.order_by('?')[:category_count]:
                game.categories.add(category)
            
            # 添加标签 (每个游戏随机2-3个标签)
            tag_count = min(3, tags.count())
            for tag in tags.order_by('?')[:tag_count]:
                game.tags.add(tag)
                
            print(f"创建了游戏: {game.title}")


if __name__ == "__main__":
    print("开始创建测试数据...")
    create_test_categories()
    create_test_tags()
    create_test_games()
    print("测试数据创建完成") 