from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Game, Membership, Advertisement
from .models_menu_settings import Menu, MenuItem, WebsiteSetting

class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class GameTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

class MembershipTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class AdvertisementTranslationOptions(TranslationOptions):
    fields = ('name',)

class MenuTranslationOptions(TranslationOptions):
    fields = ('name',)

class MenuItemTranslationOptions(TranslationOptions):
    fields = ('title',)

class WebsiteSettingTranslationOptions(TranslationOptions):
    fields = ('site_name', 'site_description', 'copyright_text', 'meta_keywords', 'meta_description')

translator.register(Category, CategoryTranslationOptions)
translator.register(Game, GameTranslationOptions)
translator.register(Membership, MembershipTranslationOptions)
translator.register(Advertisement, AdvertisementTranslationOptions)
translator.register(Menu, MenuTranslationOptions)
translator.register(MenuItem, MenuItemTranslationOptions)
translator.register(WebsiteSetting, WebsiteSettingTranslationOptions)