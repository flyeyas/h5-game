"""
后台游戏分类模型模块 - 使用核心模型替代原有模型
"""

# 从核心模块导入共享模型
from core.models import GameCategory

# 提供命名空间导入的兼容性
__all__ = ["GameCategory"]

# 重要：此文件不应有任何新的模型定义，只用于导入和重导出核心模型 