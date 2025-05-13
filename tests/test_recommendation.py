from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from games.views import HomeView
from core.models import Game, GameCategory
from games.models import FrontUser, FrontGameHistory
import random

class RecommendationAlgorithmTest(TestCase):
    """测试首页游戏推荐算法"""
    
    def setUp(self):
        """设置测试数据"""
        self.factory = RequestFactory()
        
        # 创建游戏分类
        self.category1 = GameCategory.objects.create(name="动作游戏", slug="action")
        self.category2 = GameCategory.objects.create(name="解谜游戏", slug="puzzle")
        self.category3 = GameCategory.objects.create(name="策略游戏", slug="strategy")
        
        # 创建游戏数据 - 确保有不同的评分和游玩次数组合
        self.games = []
        
        # 高评分高游玩次数
        game1 = Game.objects.create(
            title="高评分高游玩",
            slug="high-rating-high-play",
            description="测试游戏1",
            iframe_url="https://example.com/game1",
            rating=4.8,
            play_count=1000,
            status='online'
        )
        game1.categories.add(self.category1)
        self.games.append(game1)
        
        # 高评分低游玩次数
        game2 = Game.objects.create(
            title="高评分低游玩",
            slug="high-rating-low-play",
            description="测试游戏2",
            iframe_url="https://example.com/game2",
            rating=4.9,
            play_count=100,
            status='online'
        )
        game2.categories.add(self.category2)
        self.games.append(game2)
        
        # 低评分高游玩次数
        game3 = Game.objects.create(
            title="低评分高游玩",
            slug="low-rating-high-play",
            description="测试游戏3",
            iframe_url="https://example.com/game3",
            rating=3.2,
            play_count=1200,
            status='online'
        )
        game3.categories.add(self.category3)
        self.games.append(game3)
        
        # 低评分低游玩次数
        game4 = Game.objects.create(
            title="低评分低游玩",
            slug="low-rating-low-play",
            description="测试游戏4",
            iframe_url="https://example.com/game4",
            rating=3.0,
            play_count=150,
            status='online'
        )
        game4.categories.add(self.category1)
        self.games.append(game4)
        
        # 中等评分中等游玩次数
        game5 = Game.objects.create(
            title="中等评分中等游玩",
            slug="medium-rating-medium-play",
            description="测试游戏5",
            iframe_url="https://example.com/game5",
            rating=4.0,
            play_count=500,
            status='online'
        )
        game5.categories.add(self.category2)
        self.games.append(game5)
        
        # 离线游戏（不应该被推荐）
        game6 = Game.objects.create(
            title="离线游戏",
            slug="offline-game",
            description="测试游戏6",
            iframe_url="https://example.com/game6",
            rating=5.0,
            play_count=2000,
            status='offline'
        )
        game6.categories.add(self.category1)
        self.games.append(game6)
        
        # 创建测试用户
        self.user = FrontUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
    
    def test_recommendation_algorithm_anonymous(self):
        """测试匿名用户的推荐算法"""
        request = self.factory.get('/')
        request.user = None  # 匿名用户
        
        view = HomeView()
        view.request = request
        
        # 获取推荐结果
        recommended_games = view.get_recommended_games(request)
        
        # 验证结果 - 应该按照组合分数排序（评分60%权重，游玩次数40%权重）
        self.assertEqual(recommended_games.count(), 5)  # 应该有5个在线游戏
        
        # 离线游戏不应该出现在结果中
        for game in recommended_games:
            self.assertEqual(game.status, 'online')
        
        # 验证排序 - 第一个应该是高评分高游玩的游戏
        self.assertEqual(recommended_games[0].id, self.games[0].id)
        
    def test_recommendation_algorithm_with_user_history(self):
        """测试有用户历史记录时的推荐算法"""
        # 为用户创建游戏历史记录
        FrontGameHistory.objects.create(
            user=self.user,
            game=self.games[2],  # 低评分高游玩
            play_count=5
        )
        
        request = self.factory.get('/')
        request.user = self.user
        
        view = HomeView()
        view.request = request
        
        # 获取推荐结果
        recommended_games = view.get_recommended_games(request)
        
        # 用户玩过的游戏不应该出现在推荐中
        for game in recommended_games:
            self.assertNotEqual(game.id, self.games[2].id)
            
        # 同一分类的游戏应该被优先推荐
        category3_games = False
        for game in recommended_games:
            if self.category3 in game.categories.all():
                category3_games = True
                break
        
        self.assertTrue(category3_games, "用户历史相关分类的游戏应该被推荐") 