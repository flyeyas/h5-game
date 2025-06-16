from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from .models import Game, Category
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import translate_url
from django.conf import settings
from django.views.i18n import set_language
from django.contrib.auth import logout
from django.utils.translation import get_language


class HomeView(TemplateView):
    """Home page view"""
    template_name = 'games/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_games'] = Game.objects.filter(is_featured=True, is_active=True)[:6]
        context['new_games'] = Game.objects.filter(is_active=True).order_by('-created_at')[:8]
        context['popular_games'] = Game.objects.filter(is_active=True).order_by('-view_count')[:8]
        context['recommended_games'] = Game.objects.filter(is_featured=True, is_active=True)[:4]
        context['categories'] = Category.objects.filter(parent=None, is_active=True)[:6]

        # Set placeholder flags
        context['placeholder_hero_image'] = False
        context['placeholder_featured_games'] = False
        context['placeholder_popular_games'] = False
        context['placeholder_new_games'] = False
        context['placeholder_recommended_games'] = False
        context['placeholder_categories'] = False

        return context


class GameListView(ListView):
    """Game list view"""
    model = Game
    template_name = 'games/game_list.html'
    context_object_name = 'games'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Game.objects.filter(is_active=True)

        # Category filtering
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(categories=category)

        # Search filtering
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )

        # Sorting
        sort = self.request.GET.get('sort', 'latest')
        if sort == 'popular':
            queryset = queryset.order_by('-view_count')
        elif sort == 'rating':
            queryset = queryset.order_by('-rating')
        else:  # latest
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Category information
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)

        # Search information
        context['search_query'] = self.request.GET.get('q', '')
        context['sort'] = self.request.GET.get('sort', 'latest')

        # Sidebar data
        context['categories'] = Category.objects.all()
        context['popular_games'] = Game.objects.filter(is_active=True).order_by('-view_count')[:5]
        
        return context


class GameDetailView(DetailView):
    """Game detail view"""
    model = Game
    template_name = 'games/game_detail.html'
    context_object_name = 'game'
    slug_url_kwarg = 'game_slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.get_object()

        # Related games
        categories = game.categories.all()
        related_games = Game.objects.filter(
            categories__in=categories, 
            is_active=True
        ).exclude(id=game.id).distinct()[:4]
        context['related_games'] = related_games
        
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        game = self.get_object()

        # Increase view count
        game.view_count += 1
        game.save(update_fields=['view_count'])
        
        return response





class CategoryListView(ListView):
    """Category list view"""
    model = Game
    template_name = 'games/category_list.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_queryset(self):
        queryset = Game.objects.filter(is_active=True)

        # Category filtering
        category_slug = self.request.GET.get('category')
        if category_slug and category_slug != 'all':
            try:
                category = Category.objects.get(slug=category_slug)
                queryset = queryset.filter(categories=category)
            except Category.DoesNotExist:
                pass

        # Rating filtering
        rating = self.request.GET.get('rating')
        if rating:
            rating_values = rating.split(',')
            rating_filters = Q()
            for r in rating_values:
                if r == '5':
                    rating_filters |= Q(rating=5)
                elif r == '4':
                    rating_filters |= Q(rating__gte=4, rating__lt=5)
                elif r == '3':
                    rating_filters |= Q(rating__gte=3, rating__lt=4)
            if rating_filters:
                queryset = queryset.filter(rating_filters)

        # Release time filtering
        release_time = self.request.GET.get('release_time')
        if release_time and release_time != 'all':
            from datetime import datetime, timedelta
            now = datetime.now()
            if release_time == 'week':
                queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
            elif release_time == 'month':
                queryset = queryset.filter(created_at__gte=now - timedelta(days=30))
            elif release_time == 'year':
                queryset = queryset.filter(created_at__gte=now - timedelta(days=365))

        # Feature filtering
        features = self.request.GET.get('feature')
        if features:
            feature_list = features.split(',')
            # Feature filtering logic can be added here as needed
            # Currently skipped because there are no corresponding fields in the Game model

        # Sorting
        sort = self.request.GET.get('sort', 'popular')
        if sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'rating':
            queryset = queryset.order_by('-rating')
        elif sort == 'name':
            queryset = queryset.order_by('title')
        else:  # popular
            queryset = queryset.order_by('-view_count')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add category data
        context['categories'] = Category.objects.filter(parent=None, is_active=True)

        # Currently selected category
        category_slug = self.request.GET.get('category')
        if category_slug and category_slug != 'all':
            try:
                context['current_category'] = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                context['current_category'] = None
        else:
            context['current_category'] = None

        # Filter parameters
        context['selected_ratings'] = self.request.GET.get('rating', '').split(',') if self.request.GET.get('rating') else []
        context['release_time'] = self.request.GET.get('release_time', 'all')
        context['selected_features'] = self.request.GET.get('feature', '').split(',') if self.request.GET.get('feature') else []
        context['sort'] = self.request.GET.get('sort', 'popular')

        return context





def custom_set_language(request):
    """
    Custom language switching view with optimized URL handling
    Based on Django's built-in set_language view, but with improved URL conversion
    """
    # Call Django's original set_language view to handle basic language switching logic
    response = set_language(request)

    # If it's a redirect response and user specified next parameter
    if isinstance(response, HttpResponseRedirect) and request.method == 'POST':
        next_url = request.POST.get('next', request.GET.get('next'))
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            # Get the activated language
            language = translation.get_language()
            # Translate URL (handle URLs in i18n_patterns)
            try:
                # Try to generate translated URL
                translated_url = translate_url(next_url, language)
                if translated_url != next_url:
                    # If URL has changed, redirect using the new URL
                    return HttpResponseRedirect(translated_url)
            except:
                # If error occurs during translation, keep the original response
                pass
    
    return response

def custom_logout(request):
    """
    Custom logout view that supports GET method
    """
    logout(request)
    # Redirect to homepage while maintaining current language setting
    lang_code = get_language()
    return redirect(f'/{lang_code}/')