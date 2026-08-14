对应文件 [[ilina_app.py]]
# 概述
`IlinaApp` 类继承了 `QApplication`，并添加了属性用于访问各个管理器。
# 获取单例
建议使用 `ilina_app.app_instance` 函数，虽然 `QApplication.instance` 也可以使用，但前者添加了类型注释。
# 当前包括的管理器
 - theme_manager
 - plugin_manager
# IlinaApp 提供的其他方法
## 获取当前主题名
```Python
IlinaApp.get_theme_name() -> str:
```
会读取用户配置，返回当前系统颜色模式所对应的主题名。