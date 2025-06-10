#!/usr/bin/env python
"""
创建测试数据的脚本
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'html5games.settings')
django.setup()

from games.models import Category, Game, Advertisement

def create_test_data():
    """创建测试数据"""
    print("创建测试数据...")

    # 创建分类 - 扩展到8个不同类型的游戏分类
    categories = [
        {
            'name': 'Action Games',
            'slug': 'action',
            'description': 'Fast-paced action games with exciting combat and adventure',
            'icon_class': 'fa-solid fa-fist-raised',
            'order': 1
        },
        {
            'name': 'Puzzle Games',
            'slug': 'puzzle',
            'description': 'Brain-teasing puzzle games that challenge your mind',
            'icon_class': 'fa-solid fa-puzzle-piece',
            'order': 2
        },
        {
            'name': 'Adventure Games',
            'slug': 'adventure',
            'description': 'Exciting adventure games with rich storylines',
            'icon_class': 'fa-solid fa-map',
            'order': 3
        },
        {
            'name': 'Strategy Games',
            'slug': 'strategy',
            'description': 'Strategic thinking games that test your planning skills',
            'icon_class': 'fa-solid fa-chess',
            'order': 4
        },
        {
            'name': 'Racing Games',
            'slug': 'racing',
            'description': 'High-speed racing games and driving simulations',
            'icon_class': 'fa-solid fa-car',
            'order': 5
        },
        {
            'name': 'Sports Games',
            'slug': 'sports',
            'description': 'Sports simulations and athletic competitions',
            'icon_class': 'fa-solid fa-football-ball',
            'order': 6
        },
        {
            'name': 'Arcade Games',
            'slug': 'arcade',
            'description': 'Classic arcade-style games with simple but addictive gameplay',
            'icon_class': 'fa-solid fa-gamepad',
            'order': 7
        },
        {
            'name': 'Simulation Games',
            'slug': 'simulation',
            'description': 'Life and world simulation games',
            'icon_class': 'fa-solid fa-city',
            'order': 8
        }
    ]

    created_categories = []
    for cat_data in categories:
        category, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        created_categories.append(category)
        print(f"分类: {category.name} {'创建' if created else '已存在'}")
    
    # 创建游戏
    games = [
        {
            'title': 'Super Adventure',
            'slug': 'super-adventure',
            'description': 'An amazing adventure game with stunning graphics.',
            'iframe_url': 'https://example.com/game1',
            'is_featured': True,
            'categories': [created_categories[2]]  # Adventure
        },
        {
            'title': 'Puzzle Master',
            'slug': 'puzzle-master',
            'description': 'Challenge your mind with this puzzle game.',
            'iframe_url': 'https://example.com/game2',
            'is_featured': True,
            'categories': [created_categories[1]]  # Puzzle
        },
        {
            'title': 'Action Hero',
            'slug': 'action-hero',
            'description': 'Fast-paced action game with epic battles.',
            'iframe_url': 'https://example.com/game3',
            'is_featured': False,
            'categories': [created_categories[0]]  # Action
        },
        {
            'title': 'Soccer Championship',
            'slug': 'soccer-championship',
            'description': 'The ultimate soccer game experience.',
            'iframe_url': 'https://example.com/game4',
            'is_featured': False,
            'categories': [created_categories[3]]  # Sports
        },
    ]
    
    for game_data in games:
        categories = game_data.pop('categories')
        game, created = Game.objects.get_or_create(
            slug=game_data['slug'],
            defaults=game_data
        )
        if created:
            game.categories.set(categories)
        print(f"游戏: {game.title} {'创建' if created else '已存在'}")
    
    # 创建广告
    ads = [
        {
            'name': 'Header Banner',
            'position': 'header',
            'url': 'https://example.com/ad1',
            'html_code': '<div style="background: #007bff; color: white; padding: 10px; text-align: center;">Sample Header Ad</div>',
            'is_active': True
        },
        {
            'name': 'Sidebar Ad 1',
            'position': 'sidebar',
            'url': 'https://example.com/ad2',
            'html_code': '<div style="background: #28a745; color: white; padding: 15px; text-align: center; border-radius: 5px;">Sample Sidebar Ad 1</div>',
            'is_active': True
        },
        {
            'name': 'Sidebar Ad 2',
            'position': 'sidebar',
            'url': 'https://example.com/ad3',
            'html_code': '<div style="background: #dc3545; color: white; padding: 15px; text-align: center; border-radius: 5px;">Sample Sidebar Ad 2</div>',
            'is_active': True
        },
        {
            'name': 'Footer Ad',
            'position': 'footer',
            'url': 'https://example.com/ad4',
            'html_code': '<div style="background: #6f42c1; color: white; padding: 10px; text-align: center; border-radius: 5px;">Sample Footer Ad</div>',
            'is_active': True
        }
    ]
    
    for ad_data in ads:
        ad, created = Advertisement.objects.get_or_create(
            name=ad_data['name'],
            defaults=ad_data
        )
        print(f"广告: {ad.name} {'创建' if created else '已存在'}")
    
    print("测试数据创建完成！")

if __name__ == '__main__':
    create_test_data()
