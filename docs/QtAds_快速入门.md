# PySide6-QtAds 快速入门指南

> 没骗你，这东西真的跟广告没有任何关系。ADS = **Advanced Docking System**。  
> 但在代码里 `import PySide6QtAds as QtAds` 确实怎么看怎么像广告 SDK，习惯就好。

---

## 1. 这是什么？

**Qt-Advanced-Docking-System** 是一个为 Qt 打造的高级窗口停靠系统，能做出类似 Visual Studio / VSCode 那种灵活的面板布局：

- 任意拖拽、停靠、浮动面板
- 面板可以组合成标签页（tab）
- 支持 Auto-Hide（自动隐藏到侧边栏）
- 支持 **Perspectives**（一键切换整组面板布局）
- 布局可序列化/反序列化（保存 & 恢复）

`PySide6-QtAds` 是它在 PySide6 上的官方 Python 绑定。

---

## 2. 安装

```bash
pip install PySide6-QtAds
```

要求：Python ≥ 3.10，PySide6。

支持 Windows（x64/ARM64）、Linux（x64/ARM64）、macOS（x64/ARM64）。

---

## 3. 最小可运行示例

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt
import PySide6QtAds as QtAds


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QtAds 快速入门")
        self.resize(800, 600)

        # ① 创建 DockManager——整个停靠系统的核心
        self.dock_manager = QtAds.CDockManager(self)

        # ② 创建一个 DockWidget，塞入任意 QWidget
        label = QLabel("Hello, QtAds!")
        label.setAlignment(Qt.AlignCenter)

        dock = QtAds.CDockWidget("我的面板")
        dock.setWidget(label)

        # ③ 把 DockWidget 添加到左侧区域
        self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.LeftDockWidgetArea, dock
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec()
```

跑起来就能看到一个可拖拽、可关闭、可浮动的面板。

---

## 4. 核心概念

| 概念 | 对应类 | 说明 |
|---|---|---|
| **DockManager** | `CDockManager` | 停靠系统的总控制器，一个主窗口一个 |
| **DockWidget** | `CDockWidget` | 可停靠的面板，类似 `QDockWidget` 但强得多 |
| **DockAreaWidget** | `CDockAreaWidget` | 容纳多个 DockWidget 的区域（自动创建） |
| **DockWidgetArea** | 枚举 | 指定停靠方位 |

### 停靠方位 (`DockWidgetArea`)

```python
QtAds.DockWidgetArea.LeftDockWidgetArea    # 左侧
QtAds.DockWidgetArea.RightDockWidgetArea   # 右侧
QtAds.DockWidgetArea.TopDockWidgetArea     # 顶部
QtAds.DockWidgetArea.BottomDockWidgetArea  # 底部
QtAds.DockWidgetArea.CenterDockWidgetArea  # 中央（不指定边）
```

> 还有一个 `QtAds.CenterDockWidgetArea`，用于 `addDockWidgetTab()` 来在中央添加标签页。

---

## 5. 常用操作

### 5.1 添加面板到指定方位

```python
dock = QtAds.CDockWidget("面板标题")
dock.setWidget(some_widget)

# 添加到左侧
self.dock_manager.addDockWidget(QtAds.DockWidgetArea.LeftDockWidgetArea, dock)

# 添加到下方，并指定相对于哪个已有区域
self.dock_manager.addDockWidget(
    QtAds.DockWidgetArea.BottomDockWidgetArea,
    dock,
    reference_area  # 相对于这个区域
)
```

### 5.2 以标签页方式添加

```python
# 在中央区域添加一个标签页
self.dock_manager.addDockWidgetTab(
    QtAds.CenterDockWidgetArea,
    dock1
)
self.dock_manager.addDockWidgetTab(
    QtAds.CenterDockWidgetArea,
    dock2
)
# dock1 和 dock2 现在是中央区域的标签页
```

### 5.3 设置中央控件

```python
central_dock = QtAds.CDockWidget("编辑器")
central_dock.setWidget(QTextEdit())
# 设为中心控件后，该面板不可移动/不可关闭/无标题栏
area = self.dock_manager.setCentralWidget(central_dock)
```

> ⚠️ 必须先于其他任何 DockWidget 调用。

### 5.4 隐藏/显示面板

```python
dock.hide()                   # 隐藏
dock.show()                   # 显示
dock.toggleView()             # 切换显隐
action = dock.toggleViewAction()  # 获取可用于菜单栏的 QAction
```

### 5.5 删除面板（动态面板）

```python
dock = QtAds.CDockWidget("临时面板")
dock.setFeature(QtAds.CDockWidget.DockWidgetDeleteOnClose, True)
# 关闭时会真正删除整个 DockWidget，而不是仅隐藏
```

### 5.6 设置最小尺寸

```python
# 让拆分隔条能缩到更小（默认 DockWidget 的 minimumSizeHint 很小）
dock.setMinimumSizeHintMode(
    QtAds.CDockWidget.MinimumSizeHintFromDockWidget
)
# 如果要遵从内容的 minimumSizeHint：
dock.setMinimumSizeHintMode(
    QtAds.CDockWidget.MinimumSizeHintFromContent
)
```

---

## 6. 配置标志（Config Flags）

在创建 `CDockManager` **之前**设置，否则会 crash。

### 常用标志一览

```python
# === 拖拽预览 ===
QtAds.CDockManager.DragPreviewIsDynamic          # 动态拖拽预览（需关下面两个）
QtAds.CDockManager.DragPreviewShowsContentPixmap # 拖拽预览显示内容截图
QtAds.CDockManager.DragPreviewHasWindowFrame     # 拖拽预览带窗口边框

# === 分离器 ===
QtAds.CDockManager.OpaqueSplitterResize          # 拖动分离器时实时重绘（默认）
                                                   # 取消则松手后才重绘
# === 标签页 ===
QtAds.CDockManager.AllTabsHaveCloseButton        # 所有标签都有关闭按钮
QtAds.CDockManager.ActiveTabHasCloseButton       # 仅活跃标签有关闭按钮（默认）
QtAds.CDockManager.AlwaysShowTabs                # 单面板也显示标签栏
QtAds.CDockManager.TabsAtBottom                  # 标签显示在底部
QtAds.CDockManager.DoubleClickUndocksWidget      # 双击标签取消停靠

# === 焦点高亮 ===
QtAds.CDockManager.FocusHighlighting             # VS 风格的焦点高亮

# === XML 保存 ===
QtAds.CDockManager.XmlCompressionEnabled         # 保存布局时压缩 XML（默认开启）

# === 样式 ===
QtAds.CDockManager.DisableStyleheet              # 禁用手写样式表
```

### 设置方式

```python
# 方式 1：选择一个预设，再改个别标志
QtAds.CDockManager.setConfigFlags(QtAds.CDockManager.DefaultOpaqueConfig)
QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.FocusHighlighting, True)

# 方式 2：逐条设置
QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.OpaqueSplitterResize, True)
QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.XmlCompressionEnabled, False)
```

---

## 7. Auto-Hide（自动隐藏侧边栏）

类似 VS Code 中侧边栏的"折叠"功能。

```python
# ① 启用 Auto-Hide
QtAds.CDockManager.setAutoHideConfigFlags(
    QtAds.CDockManager.DefaultAutoHideConfig
)

# ② 直接把面板添加为 Auto-Hide
self.dock_manager.addAutoHideDockWidget(
    QtAds.SideBarLocation.SideBarLeft,
    dock_widget
)

# 常用 Auto-Hide 配置
QtAds.CDockManager.setAutoHideConfigFlag(
    QtAds.CDockManager.AutoHideShowOnMouseOver, True  # 鼠标悬停自动展开
)
QtAds.CDockManager.setAutoHideConfigFlag(
    QtAds.CDockManager.AutoHideSideBarsIconOnly, True  # 侧边栏只显示图标
)
```

侧边栏位置：

- `SideBarLeft` / `SideBarRight` / `SideBarTop` / `SideBarBottom`

---

## 8. 布局保存与恢复

### 保存/恢复当前布局

```python
# 保存
state = self.dock_manager.saveState()
with open("layout.json", "w") as f:
    f.write(state)

# 恢复
with open("layout.json", "r") as f:
    state = f.read()
self.dock_manager.restoreState(state)
```

### Perspectives（多套布局方案）

```python
# 保存当前布局为具名 Perspective
self.dock_manager.addPerspective("编码模式")

# 切换到指定 Perspective
self.dock_manager.openPerspective("编码模式")

# 列出所有已保存的 Perspective
names = self.dock_manager.perspectiveNames()
```

---

## 9. 样式（Stylesheet）

QtAds 自带一套内部样式表（支持亮色/暗色自动切换）。如果要自定义：

```python
# 方式 1：直接覆盖
self.dock_manager.setStyleSheet("")

# 方式 2：配置标志（在创建 CDockManager 前）
QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.DisableStyleheet, True)
```

所有组件都支持 `[focused="true"]` 属性选择器来做焦点高亮样式。

---

## 10. 锁定布局（防误触）

```python
# 锁定所有面板的关闭/移动/浮动
self.dock_manager.lockDockWidgetFeaturesGlobally()

# 解锁
self.dock_manager.lockDockWidgetFeaturesGlobally(
    QtAds.CDockWidget.NoDockWidgetFeatures
)

# 只锁定部分功能
self.dock_manager.lockDockWidgetFeaturesGlobally(
    QtAds.CDockWidget.DockWidgetClosable |
    QtAds.CDockWidget.DockWidgetMovable
)
```

---

## 11. 完整示例：一个 IDE 风格布局

```python
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QTreeWidget, QLabel
)
from PySide6.QtCore import Qt
import PySide6QtAds as QtAds


class IDEWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QtAds IDE 风格示例")
        self.resize(1200, 800)

        # --- 配置 ---
        QtAds.CDockManager.setConfigFlag(
            QtAds.CDockManager.FocusHighlighting, True
        )
        QtAds.CDockManager.setConfigFlag(
            QtAds.CDockManager.OpaqueSplitterResize, True
        )

        # --- DockManager ---
        self.dm = QtAds.CDockManager(self)

        # --- 中央：编辑器（标签页） ---
        for i in range(3):
            editor = QTextEdit()
            editor.setPlainText(f"// 文件 {i+1} 的内容...")
            dock = QtAds.CDockWidget(f"文件{i+1}.py")
            dock.setWidget(editor)
            self.dm.addDockWidgetTab(QtAds.CenterDockWidgetArea, dock)

        # --- 左侧：文件树 ---
        tree = QtAds.CDockWidget("文件浏览器")
        tree.setWidget(QTreeWidget())
        self.dm.addDockWidget(QtAds.DockWidgetArea.LeftDockWidgetArea, tree)

        # --- 底部：日志 ---
        log = QtAds.CDockWidget("输出")
        log.setWidget(QLabel("构建输出..."))
        self.dm.addDockWidget(QtAds.DockWidgetArea.BottomDockWidgetArea, log)

        # --- 右侧：属性面板 ---
        props = QtAds.CDockWidget("属性")
        props.setWidget(QLabel("属性面板"))
        self.dm.addDockWidget(QtAds.DockWidgetArea.RightDockWidgetArea, props)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = IDEWindow()
    win.show()
    app.exec()
```

---

## 12. 常见问题

### Q: 模块名/导入报错

旧版本需要用 `from PySide6QtAds import ads` 或 `QtAds.ads.CDockManager`。  
**最新版（≥4.1）直接用**：

```python
import PySide6QtAds as QtAds
# 然后直接 QtAds.CDockManager、QtAds.CDockWidget 等
```

### Q: 设置了 Config Flag 后 crash

Config Flag 必须在创建 `CDockManager` **之前**设置。确保 `setConfigFlag` 调用在 `CDockManager(self)` 前面。

### Q: 面板宽度/高度改不动

——需要设置 `MinimumSizeHintMode`：

```python
dock.setMinimumSizeHintMode(
    QtAds.CDockWidget.MinimumSizeHintFromDockWidget
)
```

### Q: 怎么让浮动窗口用系统原生标题栏？

```python
QtAds.CDockManager.setConfigFlag(
    QtAds.CDockManager.FloatingContainerForceNativeTitleBar, True
)
```

> Linux 下受窗口管理器限制，KWin 不原生支持。

---

## 13. 参考资源

| 资源 | 地址 |
|---|---|
| PySide6 绑定 GitHub | https://github.com/mborgerson/pyside6_qtads |
| 上游 C++ 项目 | https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System |
| Python 示例代码 | https://github.com/mborgerson/Qt-Advanced-Docking-System/tree/pyside6/examples |
| 用户指南（英文） | https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System/blob/master/doc/user-guide.md |
| PyPI | https://pypi.org/project/PySide6-QtAds/ |
