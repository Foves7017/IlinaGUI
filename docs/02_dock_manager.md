对应文件：[[dock_manager.py]]
# 概述
基于 PySide-QtAds 实现的 dock 布局功能。

在 IlinaGUI 中，dock 是最小的功能组件，通常来说，作为插件开发者不需要涉及到这一层，只需要提供自己插件的 dock widget 即可。

而对于整个 IlinaGUI 而言，dock manager 提供如下的功能：
1. 保存和记录每个 dock 创建时的参数
2. 保存和恢复布局
3. 在恢复布局之前，使用保存的 dock 参数重建 dock
4. 在浮动窗口创建之后，将其设置为顶级窗口并插入背景图片组件
# Dock Widget 是什么？
从技术角度讲，实际上是 QtAds 里面的 CDockWidget。

但我们这里从插件开发的角度来说，实际上指的是 CDockWidget 里面作为内容的 Widget。而这个 Widget 可以是 QWidget（QSS），也可以是 QQuickWidget（QML）
# 创建一个 Dock Widget 会传入的参数
会传入一个 pydatic 模型，保存了创建 dock 时的基础信息：
```Python
class DockInitInfo(BaseModel):
    name: str  # dock 所属的插件名称
    uuid: UUID   # 系统分配给 dock 的 UUID
    open_file: Path|None  # 传递给 dock 的文件名，None 说明是通过 active bar 按钮打开的。
```
# 默认存在的导入
```Python
from uuid import UUID
from pathlib import Path
from pydantic import BaseModel
```