# HTML5游戏平台

## 数据模型架构说明

本项目采用了共享数据模型的架构，使前台和后台共用同一套数据库模型，同时保持代码的独立性和清晰性。

### 架构设计

1. **核心模型层 (`core` 应用)**
   - 定义所有共享的数据模型（游戏、分类、标签等）
   - 不包含业务逻辑，只负责数据结构定义
   - 是前台和后台模块的数据基础

2. **前台模块 (`games` 应用)**
   - 通过导入核心模型来复用数据定义
   - 独立的视图、表单和业务逻辑
   - 不直接引用后台模块代码

3. **后台模块 (`admin_panel` 应用)**
   - 通过导入核心模型来复用数据定义
   - 独立的管理界面和业务逻辑
   - 不直接引用前台模块代码

### 数据访问方式

- 前台模块通过 `from games.models import Game, GameCategory, GameTag` 方式访问数据模型
- 后台模块通过 `from admin_panel.game import Game` 或 `from admin_panel.game_category import GameCategory` 访问数据模型
- 实际上，这些模型都是引用自 `core` 应用的同名模型

### 迁移说明

如需将现有数据迁移到新架构，请执行：

```
python manage.py makemigrations core
python manage.py migrate core
python migrate_data.py
```

### 开发注意事项

1. 数据模型的任何修改都应在 `core` 应用中进行
2. 前台和后台模块不应包含模型定义，只能从 `core` 导入
3. 保持业务逻辑与数据层的分离，业务逻辑应放在各自模块中 