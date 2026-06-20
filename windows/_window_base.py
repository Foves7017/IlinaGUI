import sys
import ctypes
import logging

from typing import Literal, Callable
from ctypes import windll, byref, sizeof
from ctypes.wintypes import HWND, INT

from FovesConfig import ConfigLoader

from PySide6 import QtWidgets
from PySide6.QtGui import QMouseEvent, QShowEvent, QIcon, QImage, QPixmap
from PySide6.QtCore import Qt, QPoint, Slot, QTimer, QByteArray, QEvent
from PySide6.QtWidgets import QApplication

from .types import WindowConfig
from QSS import qss_formatter, QSSFiles, QSSInfo

if sys.platform == 'win32':
    from win32con import (
        # # Windows 消息常量
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
        SIZE_MAXIMIZED
    )

CONFIG_PATH = 'configs/window.json'

class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth",    INT),
        ("cxRightWidth",   INT),
        ("cyTopHeight",    INT),
        ("cyBottomHeight", INT),
    ]

class MSG(ctypes.Structure):
    """Windows MSG 结构体，用于 nativeEvent 解析"""
    _fields_ = [
        ("hwnd",    ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam",  ctypes.c_ulonglong),
        ("lParam",  ctypes.c_longlong),
        ("time",    ctypes.c_uint),
        ("pt_x",    ctypes.c_long),
        ("pt_y",    ctypes.c_long),
    ]

class WindowBase(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('./images/ico.ico'))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        qss_formatter.add_widget(self, 'WindowBase', QSSFiles.window_base)
    
        # 日志
        self.log = logging.getLogger(f'窗口基类')

        # 加载配置 
        with ConfigLoader(CONFIG_PATH, WindowConfig) as conf:
            # 如果存储文件里没有缓存窗口状态，就默认启动到屏幕中心
            if conf.window_state == '':
                self.resize(*conf.default_size)
                fg = self.frameGeometry()  # 获取屏幕几何的副本
                fg.moveCenter(self.screen().availableGeometry().center())  # 把几何的副本放到中间
                self.move(fg.topLeft())  # 真的移动窗口
            else:
                self.restoreGeometry(QByteArray.fromBase64(conf.window_state.encode()))
            self.edge_board = conf.edge_board
            self.titlebar_height = conf.titlebar_height

        # 窗口
        window_layout = QtWidgets.QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)

        # 背景滤镜
        backgournd_filter_widget = QtWidgets.QWidget()
        backgournd_filter_widget.setObjectName('BackgroundFilter')
        qss_formatter.add_widget(backgournd_filter_widget, 'BackgroundFilter', QSSFiles.window_base)
        window_layout.addWidget(backgournd_filter_widget)

        # 设置根布局
        self.root_layout = QtWidgets.QVBoxLayout(backgournd_filter_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # 设置顶栏
        self.root_layout.addWidget(self._setup_topbar())

        # 加载中 Label
        self.loading_label = QtWidgets.QLabel(text='Now Loading...')
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setWordWrap(True)
        font = self.loading_label.font()
        font.setPointSize(24)
        self.loading_label.setFont(font)
        self.root_layout.addWidget(self.loading_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 标志变量
        self.Maximized: bool = False

        # 启用 DWM 阴影 + Aero Snap + 最大化动画
        self._setup_dwm()
    

    def _get_scheme(self) -> Literal['light', 'dark']:
        # 确定颜色主题
        app: QApplication = QtWidgets.QApplication.instance() # pyright: ignore[reportAssignmentType]
        with ConfigLoader(CONFIG_PATH, WindowConfig) as conf:
            if conf.scheme_setting == 'auto':
                scheme = 'dark' if app.styleHints().colorScheme() == Qt.ColorScheme.Dark else 'light'
            else:
                scheme = conf.scheme_setting
        return scheme

    def _setup_dwm(self):
        """为无边框窗口启用 DWM 阴影、Aero Snap、最大化动画（仅 Windows）

        原理：FramelessWindowHint 去掉了 WS_CAPTION，导致 DWM 不画阴影、不触发 Snap。
        这里手动加回 WS_CAPTION 等样式，再通过 WM_NCCALCSIZE 吞掉视觉上的非客户区，
        从而获得「有边框窗口的一切 DWM 福利，但肉眼看不到边框」的效果。
        """
        if sys.platform != "win32":
            return

        hwnd = HWND(int(self.winId()))
        GWL_STYLE = -16

        # 1. 读取当前窗口样式，补上 Snap / 阴影所需的标志
        style = windll.user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
        style |= WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
        windll.user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)

        # 2. 强制 DWM 重新读取窗口样式（否则不会立即生效）
        windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
        )

        # 3. 告知 DWM：使用扩展边框渲染策略
        DWMWA_NCRENDERING_POLICY = 2
        DWMNCRP_ENABLED = INT(2)
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_NCRENDERING_POLICY,
            byref(DWMNCRP_ENABLED),
            sizeof(DWMNCRP_ENABLED)
        )

        # 4. 将边框向客户区延伸 1px（肉眼不可见，但 DWM 会据此画阴影）
        margins = MARGINS(0, 0, 1, 0)
        windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, byref(margins))

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            try:
                self.reload_icon()
            except AttributeError:
                pass
        super().changeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        # 设置鼠标追踪
        self.setMouseTracking(True)
        for child in self.findChildren(QtWidgets.QWidget):
            child.setMouseTracking(True)
        # 下一帧触发重载
        QTimer.singleShot(0, self.reload_icon)
        return super().showEvent(event)

    def nativeEvent(self, eventType: QByteArray, message: int):
        """处理 Windows 原生消息，补齐无边框窗口缺失的系统行为"""
        import sys
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
            if 0 <= local_x <= self.width() and 0 <= local_y <= self.titlebar_height:
                # 但按钮区域不过度拦截，让 Qt 控件正常接收事件
                child = self.childAt(QPoint(local_x, local_y))
                if child is None or child.objectName() == 'TitleBar':
                    return True, HTCAPTION
        
        elif msg.message == WM_SIZE:
            # 捕捉来自 Areo Snap 的最大化
            # 这里没有添加SIZE_RESTORED 是因为会误识别很多情况
            if msg.wParam == SIZE_MAXIMIZED:
                self.Maximized = True
                self.reload_icon()

        return False, 0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # [DEBUG] 临时添加的每次点击刷新 QSS，为了开发方便
        # self.reload_style()
        
        if event.button() == Qt.MouseButton.LeftButton:  # 按下左键
            if self.edge_board < event.pos().y() < self.titlebar_height: 
                # 检查标题栏拖动
                child = self.childAt(event.pos())
                if child and child.objectName() == 'TitleBar':
                    # 获取 QWindow 句柄并启动系统级拖动
                    window_handle = self.window().windowHandle()
                    if window_handle:
                        if self.Maximized:
                            # 记录鼠标相对于窗口的比例 r 和屏幕坐标 m
                            mx = event.pos().x() + self.frameGeometry().left()
                            my = event.pos().y() + self.frameGeometry().top()
                            rx = event.pos().x() / self.frameGeometry().size().width()
                            ry = event.pos().y() / self.frameGeometry().size().height()
                            # 切换窗口
                            self._on_max()
    
                            def after_restore():
                                # 获取新的尺寸并计算应该移动到的左上角点
                                new_size = self.frameGeometry().size()
                                new_left = int(mx - rx * new_size.width())
                                new_top = int(my - ry * new_size.height())
                                self.move(new_left, new_top)
                                window_handle.startSystemMove()

                            QTimer.singleShot(0, after_restore)
                        else:
                            window_handle.startSystemMove()

                    event.accept()
                    return

            else:
                # 检查边缘缩放，如果是全屏就不检查
                if not self.Maximized:
                    window_handle = self.window().windowHandle()
                    edge = self._get_resize_edge(event.pos())
                    if edge and window_handle:
                        window_handle.startSystemResize(edge)
                    event.accept()
                    return
            
        return super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        # 双击缩放
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().y() < self.titlebar_height:
                child = self.childAt(event.pos())
                if child and child.objectName() == 'TitleBar':
                    self._on_max()
                    event.accept()
                    return
        return super().mouseDoubleClickEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # 如果是全屏就不改变指针
        if not self.Maximized:
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
        delete_list = []
        try:
            qss_formatter.reload(scheme)
            for widget in qss_formatter.qss_table:
                try:
                    self.log.info(f'正在为 {widget.widget.objectName()}({type(widget.widget)}) 加载 QSS：{widget.qss_filename}')
                    widget.widget.setStyleSheet(qss_formatter.get_sheet(widget.qss_filename))
                except RuntimeError as e:
                    self.log.warning(f'遇到了出错的组件，正在添加到删除列表...错误：{type(e)}:{e}')
                    delete_list.append(widget)
            qss_formatter.delete_qss_infos(delete_list)
        except AttributeError:
            self.log.warning(f'跳过了加载 QSS')
        # 如果指定了回调函数就调用
        if callback is not None:
            callback()
    
    def reload_icon(self):
        scheme = self._get_scheme()

        # 加载和设置图标
        self.icons = QImage('./images/titleButtons.png')
        if scheme == 'dark':
            self.icons.invertPixels()

        try:
            # 这个 try 的原因同上
            # 2026.6.11 不要相信签名，会报错
            self.close_button.setIcon(QIcon(QPixmap.fromImage(self.icons.copy(0, 0, 64, 64))))
            if self.Maximized:
                self.max_button.setIcon(QIcon(QPixmap.fromImage(self.icons.copy(64, 0, 64, 64))))
            else:
                self.max_button.setIcon(QIcon(QPixmap.fromImage(self.icons.copy(0, 64, 64, 64))))
            self.min_button.setIcon(QIcon(QPixmap.fromImage(self.icons.copy(0, 128, 64, 64))))
        except AttributeError:
            self.log.warning(f'跳过了设置图标')


    def _setup_topbar(self) -> QtWidgets.QWidget:
        """ 设置标题栏 """
        titlebar = QtWidgets.QWidget()
        titlebar.setFixedHeight(self.titlebar_height)
        titlebar.setObjectName('TitleBar')
        titlebar.setContentsMargins(20, 0, 0, 0)
        qss_formatter.add_qss_info(QSSInfo(
            widget=titlebar, 
            qss_filename=QSSFiles.window_base
            ))

        # 2026.6.11 所有按钮设置图标的地方都应该移动到 _load_qss_from_file

        # 关闭按钮
        self.close_button = QtWidgets.QPushButton()
        # self.close_button.setIcon(self.style().standardPixmap(QtWidgets.QStyle.StandardPixmap.SP_TitleBarCloseButton))
        self.close_button.setObjectName('TitleBarClose')
        self.close_button.setSizePolicy(
            self.close_button.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.close_button,
            qss_filename=QSSFiles.window_base
        ))
        self.close_button.pressed.connect(self._on_close)

        # 最大化/还原按钮
        self.max_button = QtWidgets.QPushButton()
        # self.max_button.setIcon(self.style().standardPixmap(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMaxButton))
        self.max_button.setObjectName('TitleBarButton')
        self.max_button.setSizePolicy(
            self.max_button.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.max_button,
            qss_filename=QSSFiles.window_base
        ))
        self.max_button.pressed.connect(self._on_max)

        # 最小化按钮
        self.min_button = QtWidgets.QPushButton()
        self.min_button.setObjectName('TitleBarButton')
        self.min_button.setSizePolicy(
            self.min_button.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.min_button,
            qss_filename=QSSFiles.window_base
        ))
        self.min_button.pressed.connect(self._on_min)

        # 布局
        self.titlebar_layout = QtWidgets.QHBoxLayout(titlebar)
        self.titlebar_layout.setContentsMargins(0, 0, 0, 0)
        self.titlebar_layout.setSpacing(0)

        # 弹性空间 → 把后面三个按钮推到最右
        self.titlebar_layout.addStretch(1)

        # 三个按钮 stretch=0，不争不抢，紧挨在一起
        self.titlebar_layout.addWidget(self.min_button)
        self.titlebar_layout.addWidget(self.max_button)
        self.titlebar_layout.addWidget(self.close_button)

        return titlebar

    @Slot()
    def _on_close(self):
        with ConfigLoader(CONFIG_PATH, WindowConfig) as conf:
            conf.window_state = self.saveGeometry().toBase64().data().decode()  # pyright: ignore[reportAttributeAccessIssue]
        self.close()
    
    @Slot()
    def _on_max(self):
        if self.Maximized:
            self.showNormal()
            self.Maximized = False
        else:
            self.showMaximized()
            self.Maximized = True
        self.reload_icon()
    
    @Slot()
    def _on_min(self):
        self.showMinimized()

    def _on_color_scheme_changed(self, scheme: Qt.ColorScheme):
        QTimer.singleShot(0, self.reload_style)
        QTimer.singleShot(0, self.reload_icon)