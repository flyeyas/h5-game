from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
import importlib
import sys
import logging
import json
import os

from admin_panel.models import ConfigSettings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = _('导入配置到数据库')
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            help=_('从JSON文件导入配置，例如 ./config.json'),
            default=None
        )
        parser.add_argument(
            '--module',
            help=_('从Python模块导入配置，例如 email_settings')
        )
        parser.add_argument(
            '--config',
            help=_('模块中的配置变量名称，例如 EMAIL_CONFIG'),
            default=None
        )
        parser.add_argument(
            '--json',
            help=_('直接提供JSON格式的配置字符串'),
            default=None
        )
        parser.add_argument(
            '--key',
            help=_('保存到数据库的键名（默认与module相同）'),
            default=None
        )
        parser.add_argument(
            '--description',
            help=_('配置描述（可选）'),
            default=''
        )
    
    def handle(self, *args, **options):
        file_path = options.get('file')
        module_name = options.get('module')
        config_name = options.get('config')
        json_str = options.get('json')
        key = options.get('key')
        description = options.get('description')
        
        config_value = None
        source_info = ""
        
        # 检查参数有效性
        if sum(bool(x) for x in [file_path, module_name, json_str]) != 1:
            self.stdout.write(
                self.style.ERROR(
                    _('必须且只能指定以下一项：--file, --module 或 --json')
                )
            )
            sys.exit(1)
        
        # 从JSON文件导入
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_value = json.load(f)
                
                # 如果没有指定key，则使用文件名(不含扩展名)作为key
                if not key:
                    key = os.path.splitext(os.path.basename(file_path))[0]
                
                source_info = f"文件 {file_path}"
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        _('无法从文件 {} 读取JSON配置: {}').format(file_path, str(e))
                    )
                )
                sys.exit(1)
        
        # 从Python模块导入
        elif module_name:
            if not config_name:
                self.stdout.write(
                    self.style.ERROR(
                        _('使用 --module 时必须指定 --config 参数')
                    )
                )
                sys.exit(1)
            
            try:
                # 构建完整模块路径
                full_module_name = f'gamehub.config.{module_name}'
                
                # 导入模块
                module = importlib.import_module(full_module_name)
                
                # 获取配置变量
                if hasattr(module, config_name):
                    config_value = getattr(module, config_name)
                    
                    # 如果没有指定key，则使用module_name作为key
                    if not key:
                        key = module_name
                    
                    source_info = f"模块 {full_module_name}.{config_name}"
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            _('配置 {} 在模块 {} 中不存在').format(config_name, module_name)
                        )
                    )
                    sys.exit(1)
            except ImportError as e:
                self.stdout.write(
                    self.style.ERROR(
                        _('无法导入配置模块 {}: {}').format(module_name, str(e))
                    )
                )
                sys.exit(1)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        _('导入配置时发生错误: {}').format(str(e))
                    )
                )
                logger.exception('导入配置时发生错误')
                sys.exit(1)
        
        # 从JSON字符串导入
        elif json_str:
            try:
                config_value = json.loads(json_str)
                
                # 必须指定key
                if not key:
                    self.stdout.write(
                        self.style.ERROR(
                            _('使用 --json 时必须指定 --key 参数')
                        )
                    )
                    sys.exit(1)
                
                source_info = "JSON字符串"
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        _('解析JSON字符串失败: {}').format(str(e))
                    )
                )
                sys.exit(1)
        
        # 保存配置到数据库
        try:
            ConfigSettings.set_config(key, config_value, description)
            self.stdout.write(
                self.style.SUCCESS(
                    _('成功将配置从{}导入到数据库，键名为 {}').format(
                        source_info, key
                    )
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    _('保存配置到数据库失败: {}').format(str(e))
                )
            )
            logger.exception('保存配置到数据库失败')
            sys.exit(1) 