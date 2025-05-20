from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
import json

from .models_menu_settings import Menu, MenuItem, WebsiteSetting, Language
from .forms_menu_settings import MenuForm, MenuItemForm, WebsiteSettingForm


class SuperUserRequiredMixin(UserPassesTestMixin):
    """检查用户是否是超级用户"""
    def test_func(self):
        return self.request.user.is_superuser


# 菜单管理视图
class MenuListView(SuperUserRequiredMixin, ListView):
    """菜单列表视图"""
    model = Menu
    template_name = 'admin/menu_list.html'
    context_object_name = 'menus'


class MenuCreateView(SuperUserRequiredMixin, CreateView):
    """创建菜单视图"""
    model = Menu
    form_class = MenuForm
    template_name = 'admin/menu_form.html'
    success_url = reverse_lazy('games:admin_menu_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Menu')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Menu created successfully.'))
        return super().form_valid(form)


class MenuUpdateView(SuperUserRequiredMixin, UpdateView):
    """更新菜单视图"""
    model = Menu
    form_class = MenuForm
    template_name = 'admin/menu_form.html'
    success_url = reverse_lazy('games:admin_menu_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Menu')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Menu updated successfully.'))
        return super().form_valid(form)


class MenuDeleteView(SuperUserRequiredMixin, DeleteView):
    """删除菜单视图"""
    model = Menu
    template_name = 'admin/menu_confirm_delete.html'
    success_url = reverse_lazy('games:admin_menu_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Menu deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# 菜单项管理视图
class MenuItemListView(SuperUserRequiredMixin, ListView):
    """菜单项列表视图"""
    model = MenuItem
    template_name = 'admin/menu_item_list.html'
    context_object_name = 'menu_items'
    
    def get_queryset(self):
        self.menu = get_object_or_404(Menu, pk=self.kwargs['menu_id'])
        return MenuItem.objects.filter(menu=self.menu, parent=None)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = self.menu
        
        # 获取所有菜单项，包括子菜单项
        all_items = MenuItem.objects.filter(menu=self.menu).order_by('parent__id', 'order')
        
        # 构建菜单树
        menu_tree = []
        for item in all_items:
            if not item.parent:
                item_data = {
                    'id': item.id, 
                    'title': item.title,
                    'url': item.url,
                    'icon': item.icon,
                    'order': item.order,
                    'is_active': item.is_active,
                    'children': []
                }
                
                # 添加子菜单项
                for child in all_items:
                    if child.parent and child.parent.id == item.id:
                        item_data['children'].append({
                            'id': child.id,
                            'title': child.title,
                            'url': child.url,
                            'icon': child.icon,
                            'order': child.order,
                            'is_active': child.is_active,
                        })
                
                menu_tree.append(item_data)
        
        context['menu_tree'] = menu_tree
        context['menu_tree_json'] = json.dumps(menu_tree)
        return context


class MenuItemCreateView(SuperUserRequiredMixin, CreateView):
    """创建菜单项视图"""
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'admin/menu_item_form.html'
    
    def get_success_url(self):
        return reverse_lazy('games:admin_menu_items', kwargs={'menu_id': self.kwargs['menu_id']})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.menu = get_object_or_404(Menu, pk=self.kwargs['menu_id'])
        kwargs['menu'] = self.menu
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Menu Item')
        context['menu'] = self.menu
        return context
    
    def form_valid(self, form):
        form.instance.menu = self.menu
        messages.success(self.request, _('Menu item created successfully.'))
        return super().form_valid(form)


class MenuItemUpdateView(SuperUserRequiredMixin, UpdateView):
    """更新菜单项视图"""
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'admin/menu_item_form.html'
    
    def get_success_url(self):
        return reverse_lazy('games:admin_menu_items', kwargs={'menu_id': self.object.menu.id})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['menu'] = self.object.menu
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Menu Item')
        context['menu'] = self.object.menu
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Menu item updated successfully.'))
        return super().form_valid(form)


class MenuItemDeleteView(SuperUserRequiredMixin, DeleteView):
    """删除菜单项视图"""
    model = MenuItem
    template_name = 'admin/menu_item_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('games:admin_menu_items', kwargs={'menu_id': self.object.menu.id})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Menu item deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# 网站设置视图
@login_required
@permission_required('games.change_websitesetting', raise_exception=True)
def website_settings(request):
    """网站设置视图"""
    settings = WebsiteSetting.get_settings()
    
    if request.method == 'POST':
        form = WebsiteSettingForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, _('Website settings updated successfully.'))
            return redirect('games:admin_website_settings')
    else:
        form = WebsiteSettingForm(instance=settings)
    
    context = {
        'title': _('Website Settings'),
        'form': form,
        'settings': settings,
    }
    
    return render(request, 'admin/website_settings.html', context)


# 语言管理视图
@login_required
@permission_required('auth.view_user', raise_exception=True)
def language_management(request):
    """语言管理视图"""
    from django.conf import settings
    import json
    import os
    
    languages = Language.objects.all().order_by('code')
    
    # 处理AJAX请求
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 更新语言状态（启用/禁用）
        if action == 'update_language_status':
            lang_code = request.POST.get('language_code')
            is_active = request.POST.get('is_active') == 'true'
            
            try:
                language = Language.objects.get(code=lang_code)
                language.is_active = is_active
                language.save()
                
                # 考虑更新Django设置中的LANGUAGES列表
                update_django_languages()
                
                return JsonResponse({
                    'success': True,
                    'message': _('Language status updated successfully.')
                })
            except Language.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': _('Language not found.'),
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
        
        # 设置默认语言
        elif action == 'set_default_language':
            lang_code = request.POST.get('language_code')
            
            try:
                language = Language.objects.get(code=lang_code)
                # 将其他语言的is_default设为False
                Language.objects.all().update(is_default=False)
                language.is_default = True
                language.save()
                
                # 考虑更新Django设置中的LANGUAGE_CODE
                from django.conf import settings
                settings.LANGUAGE_CODE = lang_code
                
                return JsonResponse({
                    'success': True,
                    'message': _('Default language set successfully.')
                })
            except Language.DoesNotExist:
                current_default = Language.objects.filter(is_default=True).first()
                return JsonResponse({
                    'success': False,
                    'message': _('Language not found.'),
                    'current_default': current_default.code if current_default else settings.LANGUAGE_CODE
                })
            except Exception as e:
                current_default = Language.objects.filter(is_default=True).first()
                return JsonResponse({
                    'success': False,
                    'message': str(e),
                    'current_default': current_default.code if current_default else settings.LANGUAGE_CODE
                })
        
        # 添加新语言
        elif action == 'add_language':
            language_name = request.POST.get('language_name')
            language_code = request.POST.get('language_code')
            language_active = 'language_active' in request.POST
            language_default = 'language_default' in request.POST
            
            # 检查语言代码是否已存在
            if Language.objects.filter(code=language_code).exists():
                messages.error(request, _('Language with this code already exists.'))
                return redirect('games:admin_language_management')
            
            # 创建新语言
            language = Language(
                name=language_name,
                code=language_code,
                is_active=language_active,
                is_default=language_default
            )
            
            # 处理语言旗帜图片
            if 'language_flag' in request.FILES:
                from easy_thumbnails.files import get_thumbnailer
                from filer.models import Image
                
                flag_image = request.FILES['language_flag']
                # 创建Filer图片对象
                image = Image.objects.create(
                    original_filename=flag_image.name,
                    file=flag_image,
                    owner=request.user
                )
                language.flag = image
            
            language.save()
            
            # 更新Django语言设置
            update_django_languages()
            
            messages.success(request, _('Language added successfully.'))
            return redirect('games:admin_language_management')
        
        # 编辑语言
        elif action == 'edit_language':
            original_code = request.POST.get('original_language_code')
            language_name = request.POST.get('language_name')
            language_code = request.POST.get('language_code')
            language_active = 'language_active' in request.POST
            language_default = 'language_default' in request.POST
            
            try:
                language = Language.objects.get(code=original_code)
                
                # 检查新语言代码是否已被其他语言使用
                if language_code != original_code and Language.objects.filter(code=language_code).exists():
                    messages.error(request, _('Another language with this code already exists.'))
                    return redirect('games:admin_language_management')
                
                language.name = language_name
                language.code = language_code
                language.is_active = language_active
                language.is_default = language_default
                
                # 处理语言旗帜图片
                if 'language_flag' in request.FILES and request.FILES['language_flag']:
                    from filer.models import Image
                    
                    flag_image = request.FILES['language_flag']
                    # 如果已有图片则更新，否则创建新图片
                    if language.flag:
                        old_image = language.flag
                        old_image.file = flag_image
                        old_image.original_filename = flag_image.name
                        old_image.save()
                    else:
                        # 创建Filer图片对象
                        image = Image.objects.create(
                            original_filename=flag_image.name,
                            file=flag_image,
                            owner=request.user
                        )
                        language.flag = image
                
                language.save()
                
                # 更新Django语言设置
                update_django_languages()
                
                messages.success(request, _('Language updated successfully.'))
            except Language.DoesNotExist:
                messages.error(request, _('Language not found.'))
            except Exception as e:
                messages.error(request, str(e))
            
            return redirect('games:admin_language_management')
        
        # 删除语言
        elif action == 'delete_language':
            language_code = request.POST.get('language_code')
            
            try:
                language = Language.objects.get(code=language_code)
                
                # 默认语言不能删除
                if language.is_default:
                    messages.error(request, _('Cannot delete default language.'))
                    return redirect('games:admin_language_management')
                
                # 删除旗帜图片
                if language.flag:
                    language.flag.delete()
                
                language.delete()
                
                # 更新Django语言设置
                update_django_languages()
                
                messages.success(request, _('Language deleted successfully.'))
            except Language.DoesNotExist:
                messages.error(request, _('Language not found.'))
            except Exception as e:
                messages.error(request, str(e))
            
            return redirect('games:admin_language_management')
        
        # 更新语言设置
        elif action == 'update_settings':
            default_language = request.POST.get('default_language')
            enable_language_switcher = 'enable_language_switcher' in request.POST
            auto_detect_language = 'auto_detect_language' in request.POST
            
            try:
                # 更新默认语言
                if default_language:
                    language = Language.objects.get(code=default_language)
                    Language.objects.all().update(is_default=False)
                    language.is_default = True
                    language.save()
                    
                    # 更新Django设置
                    from django.conf import settings
                    settings.LANGUAGE_CODE = default_language
                
                # 更新网站设置
                website_settings = WebsiteSetting.get_settings()
                website_settings.enable_language_switcher = enable_language_switcher
                website_settings.auto_detect_language = auto_detect_language
                website_settings.save()
                
                messages.success(request, _('Language settings updated successfully.'))
            except Language.DoesNotExist:
                messages.error(request, _('Selected language not found.'))
            except Exception as e:
                messages.error(request, str(e))
            
            return redirect('games:admin_language_management')
    
    # 为模板准备数据
    website_settings = WebsiteSetting.get_settings()
    default_language = Language.objects.filter(is_default=True).first()
    
    context = {
        'title': _('Language Management'),
        'languages': languages,
        'default_language': default_language.code if default_language else settings.LANGUAGE_CODE,
        'enable_language_switcher': getattr(website_settings, 'enable_language_switcher', True),
        'auto_detect_language': getattr(website_settings, 'auto_detect_language', False),
        'available_languages': settings.LANGUAGES,
    }
    
    return render(request, 'admin/language_management.html', context)

def update_django_languages():
    """更新Django语言设置，同步Language模型与settings.LANGUAGES"""
    from django.conf import settings
    
    # 获取所有激活的语言
    active_languages = Language.objects.filter(is_active=True)
    
    # 更新settings.LANGUAGES
    languages_list = [(lang.code, lang.name) for lang in active_languages]
    if languages_list:
        settings.LANGUAGES = languages_list
    
    # 如果有默认语言，更新LANGUAGE_CODE
    default_lang = Language.objects.filter(is_default=True).first()
    if default_lang:
        settings.LANGUAGE_CODE = default_lang.code
    
    # 更新CMS语言设置
    if hasattr(settings, 'CMS_LANGUAGES'):
        cms_languages = {
            1: [
                {
                    'code': lang.code,
                    'name': lang.name,
                    'fallbacks': [l.code for l in active_languages if l.code != lang.code],
                    'public': True,
                }
                for lang in active_languages
            ],
            'default': {
                'fallbacks': [default_lang.code] if default_lang else [],
                'redirect_on_fallback': True,
                'public': True,
                'hide_untranslated': False,
            }
        }
        settings.CMS_LANGUAGES = cms_languages

# 翻译内容管理视图
@login_required
@permission_required('auth.view_user', raise_exception=True)
def translation_management(request):
    """翻译内容管理视图"""
    from django.conf import settings
    from django.apps import apps
    from modeltranslation.translator import translator
    
    # 获取所有可翻译模型
    translatable_models = []
    for model_class, options in translator._registry.items():
        app_label = model_class._meta.app_label
        model_name = model_class.__name__
        
        # 获取可翻译字段
        fields = []
        for field_name in options.fields:
            fields.append({
                'name': field_name,
                'label': model_class._meta.get_field(field_name).verbose_name,
            })
        
        # 获取模型记录数
        instance_count = model_class.objects.count()
        
        translatable_models.append({
            'app_label': app_label,
            'name': model_name,
            'verbose_name': model_class._meta.verbose_name,
            'verbose_name_plural': model_class._meta.verbose_name_plural,
            'fields': fields,
            'instance_count': instance_count,
            'admin_url': f'/admin/{app_label}/{model_name.lower()}/',
        })
    
    # 获取所有激活的语言
    languages = Language.objects.filter(is_active=True)
    
    # 获取翻译完成度统计
    translation_stats = {}
    for model_info in translatable_models:
        model_class = apps.get_model(model_info['app_label'], model_info['name'])
        
        # 每个语言的统计
        for language in languages:
            if language.code == settings.LANGUAGE_CODE:
                continue  # 跳过默认语言
                
            lang_code = language.code
            if lang_code not in translation_stats:
                translation_stats[lang_code] = {
                    'language': language,
                    'models': {},
                    'total_fields': 0,
                    'translated_fields': 0,
                }
            
            # 统计该模型下翻译字段的完成情况
            total_fields = 0
            translated_fields = 0
            
            # 检查每个实例的每个翻译字段
            instances = model_class.objects.all()
            for instance in instances:
                for field in model_info['fields']:
                    field_name = field['name']
                    total_fields += 1
                    
                    # 检查翻译字段是否有值
                    trans_field_name = f"{field_name}_{lang_code}"
                    if hasattr(instance, trans_field_name):
                        if getattr(instance, trans_field_name):
                            translated_fields += 1
            
            # 添加到统计
            translation_stats[lang_code]['models'][model_info['name']] = {
                'total': total_fields,
                'translated': translated_fields,
                'percentage': round(translated_fields / total_fields * 100, 2) if total_fields > 0 else 0,
            }
            
            # 累加总计
            translation_stats[lang_code]['total_fields'] += total_fields
            translation_stats[lang_code]['translated_fields'] += translated_fields
    
    # 计算总百分比
    for lang_code, stats in translation_stats.items():
        total = stats['total_fields']
        translated = stats['translated_fields']
        stats['percentage'] = round(translated / total * 100, 2) if total > 0 else 0
    
    context = {
        'title': _('Translation Management'),
        'translatable_models': translatable_models,
        'languages': languages,
        'default_language': settings.LANGUAGE_CODE,
        'translation_stats': translation_stats,
    }
    
    return render(request, 'admin/translation_management.html', context)