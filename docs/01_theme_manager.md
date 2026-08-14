对应文件：[[theme_manager.py]]
# 概述
这个组件提供了一种统一的键值对管理方式，使得 QML 和 QSS 可以使用同一套变量，方便实现主题的统一。同时将所有键值对以 YAML 格式存储，便于管理。
# 涉及到的配置文件

`app_config/light_theme_name`：系统处于亮色模式下的配色方案名称

`app_config/dark_theme_name` ：指定了系统处于暗色模式下的配色方案名称

# 全局单例
主题管理器应该是一个全局单例，挂在于 App 之上。可以通过
# YAML 
YAML 文件保存一系列**键值对**来作为主题的具体内容。
## 格式
YAML 文件的内容应该遵从如下的格式：
```YAML
ThemeName1:
  key: value
  ...
ThemeName2:
  key: value
  ...
general:
  key: value
  ... 
```
主题管理器会加载当前指定的主题名下的所有键值对和 `general` 下的所有键值对。

> [!INFO] 无论当前主题名称，`general` 中的键值对总是会被加载，所以可将一些非颜色的数值放置于此
## 列表
特别地，`value` 可以是一个列表。例如：
```YAML
theme:
  button_color:
    - '#0000FF'
    - '#00FF00'
    - '#FF0000'
```
在所有的 YAML 解析完成之后，**所有的**列表值会随机选取一个作为固定值，上例中按钮的颜色就会在红绿蓝之中随机选择一个。
## 重复
在不同文件的**同名主题**中，如果遇到相同的键，它们会被合并为一个列表，并在最终随机选择，例如以下的三个文件，最终效果是按钮在红绿蓝之中随机选择：

```YAML
# file1.yaml
theme:
  button_color: '#0000FF'
  
# file2.yaml
theme:
  button_color: '#00FF00'

# file3.yaml
theme:
  button_color: '#FF0000'
```
## 添加 YAML 文件
可以调用如下的方法将一个 YAML 文件作为主题添加到系统中：
```Python
add_yaml(filename: str|Path) -> None
```
# QSS 文件
## 替换格式
在 QSS 文件中，可以用两个大括号表示属性引用，主题管理器会进行字符串替换。
例如：
```YAML
light:
  text_color: '#000000'
dark:
  text_color: '#FFFFFF'
general:
  text_size_pt: 10
```

```QSS
QPushButton { 
    margin: 0px;
    border: 0px;
    padding: 0px 10px;
    font-family: "Segoe Fluent Icons";
    font-size: {{text_size_pt}}pt;
    color: {{text_color}}
}
```
在替换之后，实际应用到 QWidget 的 QSS 为：
```
QPushButton { 
    margin: 0px;
    border: 0px;
    padding: 0px 10px;
    font-family: "Segoe Fluent Icons";
    font-size: 10pt;
    color: #000000
}
```
## 将 QSS 关联到 QWidget
可以调用如下的方法将 QSS 关联到 QWdiget
```Python
add_qss_widget(qwidget: QWidget, file_name: str|list[str]|Path|list[Path], object_name: str)
```
主题管理器会记录文件和组件的关联，并自动调用组件的 `setStyleSheet` 方法。如果传递的是文件列表，则会拼接这些文件。
同时，内部使用 `object_name` 标识，所以这是必须设置的。同时也会调用组件的 `setObjectName` 方法
# QML 文件
## 注入格式
在 QML 文件中，主题管理器会自动注入一个名为 `theme` 的上下文变量，可以通过这个变量的 `get` 方法获取键值对的值：
```QML
Rectangle {
	color: theme.get("background_color")
}
```
## 将 QML 关联到 QQuickWidget
可以调用如下的方法将 QML 关联到 QQuickWidget：
```Python
add_qml_widget(qqwidget: QQuickWidget, filename: str|Path, , object_name: str)
```
主题管理器会记录文件和组件的关联，并自动调用组件的 `setScource` 方法，并且不会影响代码其他地方的 `setContextProperty`。
同时，内部使用 `object_name` 标识，所以这是必须设置的。同时也会调用组件的 `setObjectName` 方法
# 重新加载
可以调用如下的方法重新从 YAML 中加载键值对，然后应用到所有关联的组件。
```Python
reload(theme_name: str|None=None)
```
这个函数会：
1. 如果指定了 `theme_name`，更新内部保存的主题名
2. 根据主题名从文件加载所有的 YAML 文件，收集键值对
3. 将键值对的列表随机固定为固定值
4. 依次刷新所有 QSS 关联的组件，会调用组件的 `setStyleSheet` 方法
5. 依次刷新所有 QML 关联的组件，会调用组件的 `setContextProperty` 和 `setScource` 方法。
6. 发送 `theme_reloaded` 信号
另外，可以直接指定主题管理器的 `theme` 属性，主题管理器会自动调用 `reload` 方法。
也可以调用 `reload_yaml` `reload_qml` `reload_qss` 来单独刷新某些组件或某类组件。
# 在 Python 中使用
主题管理器重写了 `__getattr__` 方法，可以直接使用类似 `get_theme_manager().button_color` 的方式获取值。
同时，主题管理器也重写了 `__getitem__` 方法，可以直接使用类似
 `get_theme_manager()['button_color']` 的方式获取值。
# 其他方法与属性
## 主题
通过 `theme` 方法可以获取当前的主题名。

# 默认存在的导入
```Python
from pathlib import Path
```