#!/usr/bin/env python3
# 清理未使用的代码

with open('games/views.py', 'r') as f:
    content = f.read()

# 删除ToggleFavoriteView类
toggle_view = '''
@method_decorator(login_required, name='dispatch')
class ToggleFavoriteView(View):
    """切换游戏收藏状态"""
    def post(self, request, game_id):
        # 确保是前台用户
        if not hasattr(request.user, 'is_member'):
            # 当前用户不是 FrontUser 实例（可能是 AdminUser）
            return JsonResponse({'status': 'error', 'message': _('未授权')}, status=403)
            
        # 处理用户收藏的游戏
        try:
            # 获取前台用户
            try:
                front_user = FrontUser.objects.get(username=request.user.username)
            except FrontUser.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': _('无法找到对应的前台用户')}, status=400)
                
            game = Game.objects.get(id=game_id, status='online')
            favorite, created = FrontGameFavorite.objects.get_or_create(user=front_user, game=game)
            
            if not created:  # 如果收藏已存在，则取消收藏
                favorite.delete()
                is_favorite = False
                message = _('已取消收藏')
            else:  # 新建收藏
                is_favorite = True
                message = _('已添加到收藏')
                
            return JsonResponse({
                'status': 'success',
                'message': message,
                'is_favorite': is_favorite,
                'game_id': game_id
            })
        except Game.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': _('游戏不存在')}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

'''

# 删除AddCommentView类
comment_view = '''
@method_decorator(login_required, name='dispatch')
class AddCommentView(View):
    """添加游戏评论"""
    def post(self, request, game_id):
        # 确保是前台用户
        if not hasattr(request.user, 'is_member'):
            # 当前用户不是 FrontUser 实例（可能是 AdminUser）
            return JsonResponse({
                'status': 'error', 
                'message': _('请先登录后再发表评论'),
                'redirect': True,
                'redirect_url': reverse('games:login') + f'?next=/games/{game_id}/'
            }, status=401)  # 使用401状态码表示未认证
            
        try:
            # 获取前台用户
            try:
                front_user = FrontUser.objects.get(username=request.user.username)
            except FrontUser.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': _('无法找到对应的前台用户')}, status=400)
                
            game = Game.objects.get(id=game_id, status='online')
            content = request.POST.get('content', '').strip()
            rating = int(request.POST.get('rating', 5))
            parent_id = request.POST.get('parent_id')
            
            # 验证评论内容
            if not content:
                return JsonResponse({'status': 'error', 'message': _('评论内容不能为空')}, status=400)
                
            # 创建评论
            comment = FrontGameComment()
            comment.user = front_user
            comment.game = game
            comment.content = content
            comment.rating = rating
            
            # 处理回复评论
            if parent_id:
                try:
                    parent_comment = FrontGameComment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except FrontGameComment.DoesNotExist:
                    pass
                    
            comment.save()
            
            # 更新游戏的平均评分
            avg_rating = FrontGameComment.objects.filter(game=game).aggregate(Avg('rating'))['rating__avg']
            game.rating = round(avg_rating, 1) if avg_rating else 0
            game.save(update_fields=['rating'])
            
            logger.info(f"更新游戏评分 - 游戏ID: {game_id}, 新评分: {game.rating}")
            
            return JsonResponse({'status': 'success', 'message': _('评论已添加')})
                
        except Game.DoesNotExist:
            logger.error(f"评论游戏不存在 - 游戏ID: {game_id}")
            return JsonResponse({'status': 'error', 'message': _('游戏不存在')}, status=404)
        except Exception as e:
            logger.error(f"添加评论出错 - 错误: {str(e)}, 用户ID: {request.user.id}, 游戏ID: {game_id}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

'''

# 删除SearchView类
search_view = '''
class SearchView(ListView):
    """游戏搜索视图"""
    model = Game
    template_name = 'games/search.html'
    context_object_name = 'games'
    paginate_by = 12
    
    def get_queryset(self):
        """根据搜索条件过滤游戏"""
        queryset = super().get_queryset()
        
        # 获取搜索参数
        query = self.request.GET.get('q', '')
        category = self.request.GET.get('category', '')
        tag = self.request.GET.get('tag', '')
        sort = self.request.GET.get('sort', 'popular')
        
        # 应用搜索条件
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
        
        if category:
            queryset = queryset.filter(categories__slug=category)
            
        if tag:
            queryset = queryset.filter(tags__slug=tag)
        
        # 应用排序
        if sort == 'popular':
            queryset = queryset.order_by('-play_count', '-rating')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'rating':
            queryset = queryset.order_by('-rating', '-play_count')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 添加搜索参数到上下文
        context['query'] = self.request.GET.get('q', '')
        context['category'] = self.request.GET.get('category', '')
        context['tag'] = self.request.GET.get('tag', '')
        context['sort'] = self.request.GET.get('sort', 'popular')
        
        # 添加分类和标签列表
        context['categories'] = GameCategory.objects.all()
        context['tags'] = GameTag.objects.all()
        
        # 添加页面标题
        context['title'] = '搜索游戏'
        
        return context
'''

# 从内容中删除这些未使用的视图类
content = content.replace(toggle_view, '')
content = content.replace(comment_view, '')
content = content.replace(search_view, '')

# 写回文件
with open('games/views.py', 'w') as f:
    f.write(content)

print("已删除未使用的视图类") 