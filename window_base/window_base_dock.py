import sys
import logging
from typing import Literal, Callable
from pydantic import BaseModel
from FovesConfig import ConfigLoader

from PySide6.QtGui import QMouseEvent, QShowEvent, QIcon, QImage, QPixmap
from PySide6.QtCore import QObject, Qt, QPoint, Slot, QTimer, QByteArray, QEvent
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QHBoxLayout
from PySide6.QtQuickWidgets import QQuickWidget

from utils import app_dir
from globals import get_theme_manager
from theme_manager import get_theme_manager
from .titlebar import Titlebar
from .consts import *
from manager.consts import *
from app_config import AppConfig, APP_CONFIG_PATH

from ctypes import windll, byref, sizeof
from ctypes.wintypes import HWND, INT
from win32con import (
        # Windows 消息常量
        WM_NCCALCSIZE,
        WM_NCHITTEST,
        WM_SIZE,
        # 窗口样式
        WS_CAPTION,
        WS_THICKFRAME,  
        WS_MINIMIZEBOX, 
        WS_MAXIMIZEBOX,
        # SetWindowPos 标志
        SWP_FRAMECHANGED,
        SWP_NOMOVE,
        SWP_NOSIZE,
        SWP_NOZORDER,
        SWP_NOACTIVATE,
        # NCHITTEST 返回值
        HTCAPTION,
        SIZE_RESTORED,
        SIZE_MAXIMIZED,
    )

class WindowBaseDock(QWidget):
    """ 窗口基类 """
    def __init__(self, container):
        super().__init__(container)

        self.container = container

        self._dragging = False

        # 日志
        self.log = logging.getLogger(f'窗口基类')

        # 设置窗口图标
        self.container.setWindowIcon(QIcon(str(app_dir()/'images'/'ico.ico')))
        # self.container.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.container.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.Window)
        self.container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # formatter
        self.theme_manager = get_theme_manager()
        self.theme_manager.theme = self._get_scheme()
        self.theme_manager.add_qss_widget(self, [WINDOWBASE_QSS_PATH, DOCK_MANAGER_QSS_PATH])

        # 背景部件
        background_qqwidget = QQuickWidget()
        self.theme_manager.add_qml_widget(background_qqwidget, BACKGROUND_QML_PATH)

        # 窗口布局，仅用于容纳背景部件
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(background_qqwidget)

        # 标题栏
        self.titlebar = Titlebar()
        self.titlebar.close_button_pushed.connect(self._on_close)
        self.titlebar.min_button_pushed.connect(self._on_min)
        self.titlebar.max_button_pushed.connect(self._on_max)
        self.titlebar.titlelabel.label_edited.connect(
            lambda x: self.container.setWindowTitle(x + ' - IlinaGUI')
        )

        # 根布局
        self.root_layout = QVBoxLayout(background_qqwidget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.addWidget(self.titlebar)
        self.root_layout.setSpacing(0)

        # 加载配置 
        with ConfigLoader(CONFIG_PATH, WindowConfig) as conf:
            self.edge_board = conf.edge_board

        # QTimer.singleShot(0, self.__enable_dwm)

    def showEvent(self, event: QShowEvent) -> None:
        # 设置鼠标追踪
        self.container.setMouseTracking(True)
        self.setMouseTracking(True)
        for child in self.container.findChildren(QWidget):
            child.setMouseTracking(True)
        # 设置窗口标题
        self.container.setWindowTitle(self.titlebar.titlelabel.label + ' - IlinaGUI')
        # 下一帧触发重载
        QTimer.singleShot(0, self.reload_style)
        return super().showEvent(event)

    # def __enable_dwm(self):
    #     """为无边框窗口启用 DWM 阴影、Aero Snap、最大化动画（仅 Windows）

    #     原理：FramelessWindowHint 去掉了 WS_CAPTION，导致 DWM 不画阴影、不触发 Snap。
    #     这里手动加回 WS_CAPTION 等样式，再通过 WM_NCCALCSIZE 吞掉视觉上的非客户区，
    #     从而获得「有边框窗口的一切 DWM 福利，但肉眼看不到边框」的效果。
    #     """
    #     if sys.platform != "win32":
    #         return

    #     hwnd = HWND(int(self.container.winId()))
    #     # hwnd = HWND(int(self.window_widget.winId()))
    #     GWL_STYLE = -16

    #     # 1. 读取当前窗口样式，补上 Snap / 阴影所需的标志
    #     style = windll.user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
    #     style |= WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
    #     windll.user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)

    #     # 2. 强制 DWM 重新读取窗口样式（否则不会立即生效）
    #     windll.user32.SetWindowPos(
    #         hwnd, 0, 0, 0, 0, 0,
    #         SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
    #     )

    #     # 3. 告知 DWM：使用扩展边框渲染策略
    #     DWMWA_NCRENDERING_POLICY = 2
    #     DWMNCRP_ENABLED = INT(2)
    #     windll.dwmapi.DwmSetWindowAttribute(
    #         hwnd,
    #         DWMWA_NCRENDERING_POLICY,
    #         byref(DWMNCRP_ENABLED),
    #         sizeof(DWMNCRP_ENABLED)
    #     )

    #     # 4. 将边框向客户区延伸 1px（肉眼不可见，但 DWM 会据此画阴影）
    #     margins = MARGINS(0, 0, 1, 0)
    #     windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, byref(margins))

    def _get_scheme(self) -> str:
            # 确定颜色主题
            app: QApplication = QApplication.instance() # pyright: ignore[reportAssignmentType]
            with ConfigLoader(APP_CONFIG_PATH, AppConfig) as conf:
                if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
                    return conf.dark_theme_name
                else:
                    return conf.light_theme_name
    
    def nativeEvent(self, eventType: QByteArray, message: int):
        """处理 Windows 原生消息，补齐无边框窗口缺失的系统行为"""
        if sys.platform != "win32":
            return False, 0

        msg = MSG.from_address(int(message))

        if msg.message == WM_NCCALCSIZE:
            # 吞掉非客户区：告诉系统「我的非客户区高度为 0」
            # 这样 WS_CAPTION 样式虽然在，但不会画出视觉上的标题栏和边框
            if msg.wParam:
                return True, 0

        elif msg.message == WM_NCHITTEST:
            # 在标题栏区域返回 HTCAPTION，让 DWM 的 Aero Snap 能正常触发
            # （DWM 拖拽检测依赖 WM_NCHITTEST 返回 HTCAPTION）
            x = ctypes.c_short(msg.lParam & 0xFFFF).value
            y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value

            # 屏幕坐标 → 窗口坐标
            local_x = x - self.frameGeometry().x()
            local_y = y - self.frameGeometry().y()

            # 标题栏区域返回 HTCAPTION
            if 0 <= local_x <= self.width() and 0 <= local_y <= self.theme_manager.titlebar_height:
                # 但按钮区域不过度拦截，让 Qt 控件正常接收事件
                child = self.childAt(QPoint(local_x, local_y))
                if child is None or child.objectName() == 'TitleBar':
                    return True, HTCAPTION
        
        elif msg.message == WM_SIZE:
            # 捕捉来自 Areo Snap 的最大化和还原
            if msg.wParam == SIZE_MAXIMIZED:
                self.titlebar.is_max = True
            else:
                self.titlebar.is_max = False

        return False, 0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # [DEBUG] 临时添加的每次点击刷新 QSS，为了开发方便
        # self.reload_style()
        
        if event.button() == Qt.MouseButton.LeftButton:  # 按下左键
            if self.edge_board < event.pos().y() < self.theme_manager.titlebar_height: 
                # 检查标题栏拖动
                child = self.container.childAt(event.pos())
                if child and child.objectName() == 'TitleBar' and not self._dragging:
                    # 浮动窗口的拖拽由 WM_NCHITTEST → HTCAPTION 走系统原生拖拽，
                    # 不需要（也无法）走 startDragging 自定义拖拽路径
                    if not hasattr(self.container, 'startDragging'):
                        # 直接用 Windows 原生窗口拖动
                        window_handle = self.container.window().windowHandle()
                        if window_handle:
                            window_handle.startSystemMove()
                        event.accept()
                        return

                    if self.titlebar.is_max:
                        # 记录当前鼠标在最大化窗口中的比例
                        geo = self.container.frameGeometry()
                        rx = event.pos().x() / geo.width()
                        ry = event.pos().y() / geo.height()

                        # 还原窗口
                        self._on_max()

                        def after_restore():
                            # 窗口已经变回正常大小，按相同比例算出新的拖拽偏移
                            new_w = self.container.width()   # 注意：用 width()，不是 frameGeometry()
                            new_h = self.container.height()
                            offset = QPoint(int(rx * new_w), int(ry * new_h))

                            self.container.startDragging(offset, self.container.size(), self)
                            self.grabMouse()
                            self._dragging = True

                        QTimer.singleShot(0, after_restore)

                    else:
                        # 非最大化：直接转换坐标
                        offset = self.mapTo(self.container, event.pos())
                        self.container.startDragging(offset, self.container.size(), self)
                        self.grabMouse()
                        self._dragging = True

                    event.accept()
                    return
            else:
                # 检查边缘缩放，如果是全屏就不检查
                if not self.titlebar.is_max:
                    window_handle = self.container.window().windowHandle()
                    edge = self._get_resize_edge(event.pos())
                    if edge and window_handle:
                        ret = window_handle.startSystemResize(edge)
                    event.accept()
                    return

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            self.container.moveFloating()
        # 如果是全屏就不改变指针
        if not self.titlebar.is_max:
            edges = self._get_resize_edge(event.pos())
            if edges:
                if edges & Qt.Edge.TopEdge and edges & Qt.Edge.LeftEdge:
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)       # ↖
                elif edges & Qt.Edge.TopEdge and edges & Qt.Edge.RightEdge:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)       # ↗
                elif edges & Qt.Edge.BottomEdge and edges & Qt.Edge.LeftEdge:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)       # ↙
                elif edges & Qt.Edge.BottomEdge and edges & Qt.Edge.RightEdge:
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)       # ↘
                elif edges & Qt.Edge.TopEdge or edges & Qt.Edge.BottomEdge:
                    self.setCursor(Qt.CursorShape.SizeVerCursor)         # ↕
                elif edges & Qt.Edge.LeftEdge or edges & Qt.Edge.RightEdge:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)         # ↔
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.container.finishDragging()
        self._dragging = False
        self.releaseMouse()
        return super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        # 双击缩放
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().y() < self.theme_manager.titlebar_height:
                child = self.childAt(event.pos())
                if child and child.objectName() == 'TitleBar':
                    self._on_max()
                    event.accept()
                    return
        return super().mouseDoubleClickEvent(event)

    def _get_resize_edge(self, pos: QPoint) -> Qt.Edge:
        """判断鼠标位置对应的窗口边缘"""
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        b = self.edge_board

        edges = Qt.Edge(0)
        if x < b:      edges |= Qt.Edge.LeftEdge
        if x > w - b:  edges |= Qt.Edge.RightEdge
        if y < b:      edges |= Qt.Edge.TopEdge
        if y > h - b:  edges |= Qt.Edge.BottomEdge
        return edges

    def reload_style(self, callback: Callable|None=None):
        """ 从文件重新加载样式 """
        scheme = self._get_scheme()
        # 加载 QSS
        # 有时候会在还没初始化到那里的时候就调用，这时候就先不加载（似乎是窗口渲染了但是组件还没初始化）
        try:
            self.log.info(f'重新加载样式 (颜色主题：{scheme})')
            self.theme_manager.theme = scheme
            self.theme_manager.reload()
        except AttributeError:
            self.log.warning(f'跳过了加载主题')
        # 如果指定了回调函数就调用
        if callback is not None:
            callback()
    
    @Slot()
    def _on_close(self):
        self.container.close()
    
    @Slot()
    def _on_min(self):
        self.container.showMinimized()
    
    @Slot()
    def _on_max(self):
        if self.titlebar.is_max:
            self.container.showNormal()
            # self.__enable_dwm()
            self.titlebar.is_max = False
        else:
            self.container.showMaximized()
            # self.__disable_dwm()
            self.titlebar.is_max = True

    @Slot()
    def _on_color_scheme_changed(self, scheme: Qt.ColorScheme):
        QTimer.singleShot(0, self.reload_style)