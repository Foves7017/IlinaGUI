import logging
from uuid import UUID
from pathlib import Path

from FovesLog import LoggedTask
from FovesConfig import ConfigLoader
from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import Slot, QByteArray, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QHBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6QtAds import CDockManager

from utils import set_titlebar_color, generate_uuid, NULL_UUID
from globals import app_path, APP_CONFIG_PATH, AppConfig, DockInfo
from ilina_app import app_instance
from .dock_manager import DockManager
from .loading import Loading
from .active_bar import ActiveBar
from .background import BackgroundLayer

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.log = logging.getLogger('主窗口')

        # 加载配置 
        with ConfigLoader(APP_CONFIG_PATH, AppConfig) as conf:
            # 如果存储文件里没有缓存窗口状态，就默认启动到屏幕中心
            if conf.not_in_ui__main_window_state_ == '':
                self.resize(1440, 960)
                fg = self.frameGeometry()  # 获取屏幕几何的副本
                fg.moveCenter(self.screen().availableGeometry().center())  # 把几何的副本放到中间
                self.move(fg.topLeft())  # 真的移动窗口
            else:
                self.restoreGeometry(QByteArray.fromBase64(conf.not_in_ui__main_window_state_.encode()))

        # 设置窗口
        self.setWindowTitle(f'Ilina GUI')

        app = app_instance()
        app.theme_manager.add_qss_widget(self, app_path()/'main_window'/'main_window.qss', 'main_winndow')

        # 加载界面
        self.loading = Loading()
        app.plugin_manager.start_load_plugin.connect(self.on_plugin_load)
        app.plugin_manager.all_plugin_loaded.connect(self.on_all_plugins_loaded)

        # 背景层
        self.background_layer = BackgroundLayer()
        self.background_layer.hide()

        # 窗口布局，放背景层或者加载页面
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.loading)
        layout.addWidget(self.background_layer)

    @Slot()
    def on_all_plugins_loaded(self):
        """ 这里是在插件加载完成之后，正式开始构建主界面元素的地方 """
        with LoggedTask('构建主界面', self.log) as task:
            self.loading.deleteLater()
            task.checkpoint('删除加载界面')

            app_instance().theme_manager.reload_yaml(app_instance().get_theme_name())
            task.checkpoint('加载 YAML')

            # 设置背景
            self.background_layer.show()
            task.checkpoint('设置背景')

            # 活动栏
            self.active_bar = ActiveBar()
            self.active_bar.button_clicked.connect(lambda name: self.create_dock(name, None, None))
            self.background_layer.root_layout.addWidget(self.active_bar)
            task.checkpoint('添加活动栏')

            # Dock 管理器
            CDockManager.setConfigFlag(CDockManager.DisableStylesheet, True)
            CDockManager.setConfigFlag(CDockManager.AllTabsHaveCloseButton, True)
            CDockManager.setConfigFlag(CDockManager.DockAreaHasUndockButton, False)
            CDockManager.setConfigFlag(CDockManager.DockAreaHasTabsMenuButton, False)
            self.dock_manager = DockManager(self)
            self.background_layer.root_layout.addWidget(self.dock_manager)
            task.checkpoint('添加 Dock 管理器')

            app_instance().theme_manager.reload(app_instance().get_theme_name())
            task.checkpoint('刷新加载主题')

    @Slot()
    def create_dock(self, plugin_name: str, openfile: str|Path|None=None, uuid: UUID|None=None):
        """ 创建dock的入口，会构造内容组件实例和 DockInfo，之后传递给 Dock 管理器 """
        if isinstance(openfile, str):
            openfile = Path(openfile)

        if not uuid:
            uuid = generate_uuid()

        try:
            plug_info = app_instance().plugin_manager.plugins[plugin_name]
        except KeyError:
            self.log.error(f'未知的插件 [{plugin_name}]')
            return

        if plug_info.dock_widget:
            dock_info = DockInfo(
                plugin_name=plug_info.name,
                plugin_display_name=plug_info.display_name,
                uuid=uuid,
                openfile=openfile
            )
        else:
            self.log.error(f'插件 {plug_info.name} 没有 Dock 组件')
            return

        try:
            content_widget = plug_info.dock_widget(dock_info) # pyright: ignore[reportArgumentType, reportCallIssue]
        except Exception as e:
            from traceback import format_tb
            self.log.error(f'创建内容组件时出现错误：{repr(e)}\n{'\n'.join(format_tb(e.__traceback__))}')
            return

        self.dock_manager.create_dock(dock_info, content_widget)


    @Slot()
    def on_plugin_load(self, name: str):
        self.loading.info.setText(f'正在加载插件 {name}')

    def closeEvent(self, event: QCloseEvent) -> None:
        with ConfigLoader(APP_CONFIG_PATH, AppConfig) as conf:
            conf.not_in_ui__main_window_state_ = self.saveGeometry().toBase64().data().decode()  # pyright: ignore[reportAttributeAccessIssue]
        return super().closeEvent(event)