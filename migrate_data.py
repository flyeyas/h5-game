import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehub.settings')
django.setup()

import logging
from django.db import transaction
from django.conf import settings
from django.utils.text import slugify

# 配置日志，使用项目统一的日志级别
log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_categories():
    """迁移游戏分类数据"""
    from admin_panel.game_category import GameCategory as OldCategory
    from core.models import GameCategory as NewCategory
    
    logger.info("开始迁移游戏分类数据...")
    
    try:
        with transaction.atomic():
            # 迁移无父级的分类
            old_categories = OldCategory.objects.filter(parent=None)
            for old_cat in old_categories:
                new_cat, created = NewCategory.objects.get_or_create(
                    name=old_cat.name,
                    defaults={
                        'slug': old_cat.alias or slugify(old_cat.name),
                        'description': old_cat.description,
                        'icon': old_cat.icon,
                        'color': old_cat.color,
                        'order': old_cat.order,
                        'is_active': old_cat.is_active,
                    }
                )
                if created:
                    logger.info(f"创建了顶级分类: {new_cat.name}")
                    
                # 迁移子分类
                for old_child in old_cat.children.all():
                    new_child, child_created = NewCategory.objects.get_or_create(
                        name=old_child.name,
                        defaults={
                            'slug': old_child.alias or slugify(old_child.name),
                            'description': old_child.description,
                            'icon': old_child.icon,
                            'color': old_child.color,
                            'order': old_child.order,
                            'is_active': old_child.is_active,
                            'parent': new_cat,
                        }
                    )
                    if child_created:
                        logger.info(f"创建了子分类: {new_child.name} (父级: {new_cat.name})")
        
        logger.info("游戏分类数据迁移完成")
    except Exception as e:
        logger.error(f"游戏分类数据迁移失败: {str(e)}")
        raise


def migrate_tags():
    """迁移游戏标签数据"""
    from admin_panel.game import GameTag as OldTag
    from core.models import GameTag as NewTag
    
    logger.info("开始迁移游戏标签数据...")
    
    try:
        with transaction.atomic():
            old_tags = OldTag.objects.all()
            for old_tag in old_tags:
                new_tag, created = NewTag.objects.get_or_create(
                    name=old_tag.name,
                    defaults={
                        'slug': slugify(old_tag.name),
                        'is_active': old_tag.is_active,
                    }
                )
                if created:
                    logger.info(f"创建了标签: {new_tag.name}")
        
        logger.info("游戏标签数据迁移完成")
    except Exception as e:
        logger.error(f"游戏标签数据迁移失败: {str(e)}")
        raise


def migrate_games():
    """迁移游戏数据"""
    from admin_panel.game import Game as OldGame
    from core.models import Game as NewGame, GameCategory
    
    logger.info("开始迁移游戏数据...")
    
    try:
        with transaction.atomic():
            old_games = OldGame.objects.all()
            for old_game in old_games:
                # 创建新游戏
                new_game, created = NewGame.objects.get_or_create(
                    title=old_game.name,
                    defaults={
                        'slug': slugify(old_game.name),
                        'description': old_game.description,
                        'thumbnail': old_game.thumbnail,
                        'iframe_url': old_game.iframe_url,
                        'iframe_width': old_game.iframe_width,
                        'iframe_height': old_game.iframe_height,
                        'status': old_game.status,
                        'play_count': old_game.player_count,
                        'rating': old_game.rating,
                        'meta_title': old_game.meta_title,
                        'meta_description': old_game.meta_description,
                        'meta_keywords': old_game.meta_keywords,
                    }
                )
                
                if created:
                    logger.info(f"创建了游戏: {new_game.title}")
                    
                    # 添加分类
                    if old_game.category:
                        try:
                            new_category = GameCategory.objects.get(name=old_game.category.name)
                            new_game.categories.add(new_category)
                            logger.info(f"为游戏 {new_game.title} 添加了分类: {new_category.name}")
                        except GameCategory.DoesNotExist:
                            logger.warning(f"找不到分类 {old_game.category.name} 用于游戏 {new_game.title}")
                    
                    # 添加标签
                    for old_tag in old_game.tags.all():
                        try:
                            from core.models import GameTag
                            new_tag = GameTag.objects.get(name=old_tag.name)
                            new_game.tags.add(new_tag)
                            logger.info(f"为游戏 {new_game.title} 添加了标签: {new_tag.name}")
                        except GameTag.DoesNotExist:
                            logger.warning(f"找不到标签 {old_tag.name} 用于游戏 {new_game.title}")
        
        logger.info("游戏数据迁移完成")
    except Exception as e:
        logger.error(f"游戏数据迁移失败: {str(e)}")
        raise


def run_migration():
    """运行所有数据迁移"""
    try:
        logger.info("开始数据迁移过程...")
        
        # 按顺序执行迁移
        migrate_categories()
        migrate_tags()
        migrate_games()
        
        logger.info("所有数据迁移完成!")
    except Exception as e:
        logger.error(f"数据迁移失败: {str(e)}")


if __name__ == "__main__":
    run_migration() 