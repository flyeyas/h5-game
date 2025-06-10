from django.core.management.base import BaseCommand
from games.models import Category


class Command(BaseCommand):
    help = '创建游戏分类测试数据'

    def handle(self, *args, **options):
        self.stdout.write('开始创建分类测试数据...')
        
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

        created_count = 0
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 创建分类: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- 分类已存在: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n完成！共创建了 {created_count} 个新分类')
        )
        self.stdout.write(f'总分类数量: {Category.objects.count()}')
