对应文件：[[plugin_manager.py]]
# 概述
基于 Python 的导入机制实现的插件功能。一个插件就是一个 Python 包，通过 `__init__.py` 可以配置许多功能。

插件的设计应该遵循以下原则：
1. 插件应该是功能的最小单位，即一个插件只应该提供一个 dock（不包括设置，设置界面应该由 GUI 统一管理）如果你希望产生多个 dock，那么考虑将这些功能拆分成多个插件。
2. 允许插件之间的依赖，例如插件 A 需要依赖并使用插件 B 的功能，只需要使用 Python 的相对导入即可。并请注意不要产生循环依赖。
# 在插件中使用第三方库
只需要在插件文件夹中放置 `requirements.txt`，插件管理器就会自动识别并安装到运行环境中。
# 插件管理器发出的信号
## 开始加载插件
`start_load_plugin = Signal(str)`
会在开始加载插件时发出，参数为插件名
## 全部插件加载完成
`all_plugin_loaded = Signal()`
会在所有插件都加载完成之后发出。
# 插件中可以存在的导入名称
以下的所有名称都是可选的
## THEME_YAML
类型：`Path` 或 `list[Path]`
指定一个（些）保存了主题的 YAML 文件，这个（些）文件会被添加进主题管理器中。
建议使用 `globals.plugin_path()/'your_plugin_name'/'your_yaml_name.yaml'` 的格式来指定这一项。否则，这一项的值应该是指向 YAML 文件的**绝对路径**。
## DISPLAY_NAME
类型：`str`
插件在各种地方的显示名称，如果未指定，则会使用文件夹名称作为替代
## DOCK_WIDGET
类型：`QWidget` 或 `QQuickWidget`
当插件相关的 dock 被创建时，这个组件会作为 dock 的内容。
目前，dock 会在以下情况被创建：
 - 如果指定了活动栏按钮，则在点击活动栏时创建
 - 如果关联了某种文件格式，则在 file_manager 中双击文件时创建
在组件被初始化时，会传递如下的参数：
 - `uuid: uuid.UUID`：分配给 dock 的 uuid
 - `file: str`: 在 file_manager 中双击的文件，如果时通过活动栏创建，这个字段会被设置为 `ActiveBar`
参见：[[02_dock_manager#Dock Widget 是什么？]]
## ACTIVE_BAR_ICON_CHARA
类型：`str`
当指定了这个，会在活动栏创建一个按钮。点击这个按钮是，会创建一个 dock。
`ACTIVE_BAR_ICON_CHARA` 应该是一个单字符的字符串，并且会以 `FluentSystemIcons-Regular` 字体渲染来作为按钮图标。
这个条目只有在成功导入了 `DOCK_WIDGET` 之后才会检查
## CONFIG_MODEL
类型：`ConfigPage`
传递给配置管理器的内容，用于向配置管理器中添加条目


## CONNECTED_FILES
类型：`str` 或 `list[str]`
这是一个”通配符模式“，或者说”名称过滤器“，总之可以是类似 `*.txt` 或者 `['*.txt', '*.pdf']` 这样的东西。
它的用处是关联 dock widget 和某种文件格式，这样当在 file_manager 插件中双击文件名之后，就会创建 dock widget 并出传递这个文件名

# 默认存在的导入
```Python
from PySide6.QtWidget import QWidget
from PySide6.QtQuickWidgets import QQuickWidget
```