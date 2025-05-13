"""
脚本：更新所有游戏的slug字段
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

from core.models import Game

def update_slugs():
    """
    更新所有游戏的slug字段
    """
    games = Game.objects.all()
    for game in games:
        old_slug = game.slug
        game.slug = ''  # 清空slug，让save方法重新生成
        game.save()
        print(f'更新游戏 ID: {game.id}, 标题: {game.title}')
        print(f'旧slug: {old_slug} -> 新slug: {game.slug}')
        print('-' * 50)

if __name__ == '__main__':
    print('开始更新游戏slug...')
    update_slugs()
    print('所有游戏slug已更新完成!') 