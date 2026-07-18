# QAbstractNativeEventFilter 教程

> 当你已经不是顶层窗口了，`nativeEvent()` 再也收不到消息——  
> 这时候你需要一个全局监听器来兜底。

---

## 1. 这是什么？

`QAbstractNativeEventFilter` 是 Qt 提供的一个**全局原生事件过滤器**接口。它能拦截**整个应用**收到的所有平台原生消息（Windows 的 `MSG`、Linux/X11 的 `xcb_generic_event_t`、macOS 的 `NSEvent`），在你的 Qt 代码得到它们**之前**进行处理。

和 `QWidget.nativeEvent()` 的核心区别：

| | `nativeEvent()` | `QAbstractNativeEventFilter` |
|---|---|---|
| 作用域 | 单个 widget（且必须是**顶层窗口**才能收到窗口级消息） | 整个 QApplication |
| 注册方式 | 重写虚函数 | 实现接口 → `app.installNativeEventFilter()` |
| 典型场景 | 无边框窗口处理 `WM_NCCALCSIZE`/`WM_NCHITTEST` | 拦截**不属于自己**的窗口消息（如第三方库创建的顶层窗口） |

---

## 2. 什么时候必须用它？

一句话：**当你要拦截的消息发往一个你不拥有（也不能重写）的顶层窗口时。**

### 典型场景：QtAds 浮动窗口问题

在 IlinaGUI 中，我们需要为 QtAds 的 `CFloatingDockContainer`（浮动窗口）改装无边框效果 + DWM 阴影 + Aero Snap。

问题来了：

```
CFloatingDockContainer (顶层, HWND)  ← 这是 C++ 内部 new 的，你无法改它
└── QVBoxLayout
    └── WindowBaseII (child widget)  ← 你的自定义无边框容器
        ├── Titlebar
        └── CDockContainerWidget
```

`WindowBaseII` 只是一个 child widget，它重写的 `nativeEvent()` **永远不会收到**发给 `CFloatingDockContainer` 这个顶层窗口的 `WM_NCCALCSIZE`、`WM_NCHITTEST`、`WM_SIZE` 等消息。

**解决方案**：用一个全局的 `QAbstractNativeEventFilter`，按 HWND 把消息路由到对应的浮动容器处理逻辑。

---

## 3. 基本用法

### 3.1 实现接口

```python
from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray


class MyNativeFilter(QAbstractNativeEventFilter):
    def nativeEventFilter(self, event_type: QByteArray, message: int):
        """返回 (bool, int)：是否已处理, 返回值"""
        # event_type: 平台标识，如 "windows_generic_MSG"、"xcb_generic_event_t"
        # message: 指向原生消息结构的指针（Windows 上是 MSG*）
        
        # 这里处理你需要拦截的消息...
        
        return False, 0  # False = 未处理，继续传递给 Qt
```

### 3.2 注册与卸载

```python
from PySide6.QtWidgets import QApplication

app = QApplication([])

filter = MyNativeFilter()
app.installNativeEventFilter(filter)

# ... 应用运行 ...

# 不需要时卸载
app.removeNativeEventFilter(filter)
```

注册后，**所有**发往应用的原生消息都会先经过 `nativeEventFilter()`。

---

## 4. 平台差异

`event_type` 的值取决于操作系统：

| 平台 | `event_type` | `message` 类型 |
|---|---|---|
| Windows | `b"windows_generic_MSG"` | `MSG*`（ctypes 指针） |
| Linux (X11) | `b"xcb_generic_event_t"` | `xcb_generic_event_t*` |
| macOS | `b"mac_generic_NSEvent"` | `NSEvent*` |
| Linux (Wayland) | — | 不支持 |

> ⚠️ Wayland 下无法拦截原生事件——这是 Wayland 协议的安全设计，不是 Qt 的限制。

---

## 5. Windows 实战：拦截 MSG

在 Windows 上，`message` 参数是一个指向 `MSG` 结构体的指针。我们需要用 ctypes 读取它。

### 5.1 定义 MSG 结构体

```python
import ctypes
from ctypes import wintypes


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]
```

### 5.2 按 HWND 路由消息

这是核心设计模式：一个 filter 管理多个目标窗口。

```python
from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray
import sys


class FloatingContainerNativeFilter(QAbstractNativeEventFilter):
    """全局原生事件过滤器：按 HWND 路由消息到对应容器"""

    def __init__(self):
        super().__init__()
        self._containers: dict[int, object] = {}  # HWND → container 元数据

    def register(self, hwnd: int, container, titlebar_height: int):
        """注册一个需要拦截消息的顶层窗口"""
        self._containers[hwnd] = {
            "container": container,
            "titlebar_height": titlebar_height,
        }

    def unregister(self, hwnd: int):
        """注销"""
        self._containers.pop(hwnd, None)

    def nativeEventFilter(self, event_type: QByteArray, message: int):
        if sys.platform != "win32":
            return False, 0
        if event_type != QByteArray(b"windows_generic_MSG"):
            return False, 0

        msg = MSG.from_address(message)
        hwnd = msg.hwnd

        # 只处理已注册的窗口
        if hwnd not in self._containers:
            return False, 0

        info = self._containers[hwnd]
        return self._handle_msg(msg, info)

    def _handle_msg(self, msg, info) -> tuple[bool, int]:
        # 具体消息处理逻辑...
        pass
```

### 5.3 处理 WM_NCCALCSIZE——吞掉非客户区

```python
from win32con import WM_NCCALCSIZE


def _handle_msg(self, msg, info) -> tuple[bool, int]:
    if msg.message == WM_NCCALCSIZE:
        if msg.wParam:
            # 告诉系统：非客户区高度为 0
            # 这样 WS_CAPTION 样式虽然在，但不会画出视觉标题栏
            return True, 0
    # ...
    return False, 0
```

### 5.4 处理 WM_NCHITTEST——标题栏拖拽 + Aero Snap

```python
from win32con import WM_NCHITTEST, HTCAPTION


def _handle_msg(self, msg, info) -> tuple[bool, int]:
    if msg.message == WM_NCHITTEST:
        # 从 lParam 提取屏幕坐标
        x = ctypes.c_short(msg.lParam & 0xFFFF).value
        y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value

        container = info["container"]
        titlebar_h = info["titlebar_height"]

        # 屏幕坐标 → 客户区坐标
        geo = container.frameGeometry()
        local_x = x - geo.x()
        local_y = y - geo.y()

        # 在标题栏高度范围内 → 返回 HTCAPTION
        if 0 <= local_x <= geo.width() and 0 <= local_y <= titlebar_h:
            return True, HTCAPTION

    return False, 0
```

> `HTCAPTION` 是 Windows 的"魔法返回值"——DWM 看到它就会触发 Aero Snap、窗口拖动等系统行为。

### 5.5 处理 WM_SIZE——同步最大化状态

```python
from win32con import WM_SIZE, SIZE_MAXIMIZED


def _handle_msg(self, msg, info) -> tuple[bool, int]:
    if msg.message == WM_SIZE:
        container = info["container"]
        if msg.wParam == SIZE_MAXIMIZED:
            container.titlebar.is_max = True
        else:
            container.titlebar.is_max = False

    return False, 0
```

---

## 6. 全局单例模式

由于一个 `QApplication` 只需要一个 native event filter，使用全局单例很方便：

```python
_filter: FloatingContainerNativeFilter | None = None


def get_filter() -> FloatingContainerNativeFilter:
    global _filter
    if _filter is None:
        _filter = FloatingContainerNativeFilter()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().installNativeEventFilter(_filter)
    return _filter
```

使用方只需：

```python
f = get_filter()
f.register(int(container.winId()), container, titlebar_height=40)

# 窗口销毁时
container.destroyed.connect(lambda: f.unregister(int(container.winId())))
```

---

## 7. 完整示例：为任意 QWidget 顶层窗口注入无边框行为

下面是一个可直接运行的完整示例，演示如何用 `QAbstractNativeEventFilter` 为**多个**无边框窗口统一处理 DWM 消息。

```python
import sys
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray, Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
)

# ── Windows 常量 ──────────────────────────────────
WM_NCCALCSIZE = 0x0083
WM_NCHITTEST  = 0x0084
HTCAPTION     = 2


# ── MSG 结构体 ────────────────────────────────────
class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd",    wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam",  wintypes.WPARAM),
        ("lParam",  wintypes.LPARAM),
        ("time",    wintypes.DWORD),
        ("pt",      POINT),
    ]


# ── 全局过滤器 ────────────────────────────────────
class BorderlessHelper(QAbstractNativeEventFilter):
    """为已注册的无边框窗口提供标题栏拖拽和 Aero Snap"""

    def __init__(self):
        super().__init__()
        self._windows: dict[int, QWidget] = {}

    def register(self, widget: QWidget):
        self._windows[int(widget.winId())] = widget

    def unregister(self, widget: QWidget):
        self._windows.pop(int(widget.winId()), None)

    def nativeEventFilter(self, event_type: QByteArray, message: int):
        if event_type != QByteArray(b"windows_generic_MSG"):
            return False, 0

        msg = MSG.from_address(message)
        w = self._windows.get(msg.hwnd)
        if w is None:
            return False, 0

        if msg.message == WM_NCCALCSIZE and msg.wParam:
            return True, 0  # 吞非客户区

        if msg.message == WM_NCHITTEST:
            x = ctypes.c_short(msg.lParam & 0xFFFF).value
            y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
            geo = w.frameGeometry()
            local_x = x - geo.x()
            local_y = y - geo.y()
            # 顶部 40px → 可拖动标题栏
            if 0 <= local_x <= geo.width() and 0 <= local_y <= 40:
                return True, HTCAPTION

        return False, 0


# ── 无边框窗口 ────────────────────────────────────
class FramelessWindow(QWidget):
    def __init__(self, title: str, helper: BorderlessHelper):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: #2b2b2b; color: white;")
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 自定义标题栏
        bar = QWidget()
        bar.setFixedHeight(40)
        bar.setStyleSheet("background: #1e1e1e;")
        bar_layout = QVBoxLayout(bar)
        bar_layout.addWidget(QLabel(f"  {title}"))

        layout.addWidget(bar)
        layout.addWidget(QLabel("  拖拽顶部标题栏试试 Aero Snap", self))
        layout.addStretch()

        # 注册到全局过滤器
        helper.register(self)

    def closeEvent(self, event):
        helper.unregister(self)
        super().closeEvent(event)


# ── 启动 ──────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)

    helper = BorderlessHelper()
    app.installNativeEventFilter(helper)

    win1 = FramelessWindow("窗口 1", helper)
    win1.show()

    win2 = FramelessWindow("窗口 2", helper)
    win2.show()

    app.exec()
```

---

## 8. 与 `nativeEvent()` 的对比总结

```
                     ┌──────────────────────────────────┐
                     │        QApplication               │
                     │                                   │
  ┌──────────────┐   │   ┌──────────────────────────┐   │
  │ 原生消息队列  │───▶│   │ QAbstractNativeEventFilter │   │  ← 第一道关卡
  └──────────────┘   │   │ (全局，所有消息都经过)       │   │
                     │   └──────────┬───────────────┘   │
                     │              │ 未拦截的消息继续    │
                     │   ┌──────────▼───────────────┐   │
                     │   │ QWidget.nativeEvent()     │   │  ← 第二道关卡
                     │   │ (仅顶层窗口能收到窗口消息) │   │
                     │   └──────────┬───────────────┘   │
                     │              │                    │
                     │   ┌──────────▼───────────────┐   │
                     │   │ Qt 事件系统 / signal/slot │   │
                     │   └──────────────────────────┘   │
                     └──────────────────────────────────┘
```

**选型指南**：

| 你的情况 | 用什么 |
|---|---|
| 你拥有顶层窗口的代码，可以直接重写 | `nativeEvent()` |
| 顶层窗口是第三方库创建的（如 QtAds） | `QAbstractNativeEventFilter` |
| 需要拦截**所有**窗口的消息做全局处理 | `QAbstractNativeEventFilter` |
| 只需要拦截某个 child widget 的事件 | 都不需要，用 `eventFilter()` |

---

## 9. 注意事项

1. **性能**：`nativeEventFilter()` 会在**每条**原生消息到达时被调用。如果你注册了大量窗口，尽量在函数开头做快速过滤（如按 HWND 查字典），不要做耗时操作。

2. **返回值含义**：
   - `(True, result)` → 消息已处理，Qt 不再继续传递
   - `(False, 0)` → 消息未处理，继续传递给下一个 filter 或 Qt 内部

3. **跨平台**：如果你只关心 Windows，务必检查 `event_type == b"windows_generic_MSG"`，否则在其他平台会拿到不同类型的指针，强行按 `MSG` 解析会崩溃。

4. **多 filter 顺序**：`installNativeEventFilter()` 安装的 filter 按**后装先调**的顺序执行。如果某个 filter 返回 `True`，后面的 filter 不会收到该消息。

5. **Wayland 不支持**：在 Wayland 下 `nativeEventFilter()` 不会被调用，这是协议层面的限制，无法绕过。

---

## 10. 参考资源

| 资源 | 地址 |
|---|---|
| Qt 官方文档 | https://doc.qt.io/qt-6/qabstractnativeeventfilter.html |
| PySide6 文档 | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QAbstractNativeEventFilter.html |
| Windows MSG 结构 | https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-msg |
| WM_NCHITTEST 文档 | https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-nchittest |
