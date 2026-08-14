from logging import getLogger
from typing import cast

from FovesConfig import ConfigLoader
from PySide6.QtCore import QThread, Qt, Slot, QTimer
from PySide6.QtWidgets import QApplication

from theme_manager import ThemeManager
from plugin_manager import PluginManager
from globals import APP_CONFIG_PATH, AppConfig

class IlinaApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        # 日志
        self.log = getLogger('IlinaApp')

        # 主题管理器
        self.theme_manager = ThemeManager(None)
        # 颜色主题改变时，重载主题并刷新组件
        self.styleHints().colorSchemeChanged.connect(self.on_color_scheme_changed)

        # 插件管理器
        self.plugin_manager = PluginManager(None)
        self.load_plugin_in_thread()

    def load_plugin_in_thread(self):
        """ 在另一个线程中加载插件 """
        plugin_load_thread = QThread()
        plugin_load_thread.setObjectName('插件加载线程')
        plugin_load_thread.started.connect(self.plugin_manager.load_plugin)

        def on_all_plugin_loaded():
            """ 将所有插件完成后的行为 """
            # 1. 将管理器移回主线程
            self.plugin_manager.moveToThread(self.thread())

            # 2. 删除线程
            plugin_load_thread.quit()
            plugin_load_thread.finished.connect(plugin_load_thread.deleteLater)

        self.plugin_manager.all_plugin_loaded.connect(on_all_plugin_loaded)

        self.plugin_manager.moveToThread(plugin_load_thread)
        plugin_load_thread.start()

    def get_theme_name(self) -> str:
        # 确定颜色主题
        with ConfigLoader(APP_CONFIG_PATH, AppConfig) as conf:
            if self.styleHints().colorScheme() == Qt.ColorScheme.Dark:
                return conf.dark_theme_name
            else:
                return conf.light_theme_name

    @Slot()
    def on_color_scheme_changed(self):
        """ 主要负责在系统主题切换时重载，但也负责在首次加载插件之后重载 """
        theme_name = self.get_theme_name()
        self.theme_manager.reload(theme_name)
        self.log.info(f'系统颜色主题切换，新的主题名为：{theme_name}')

def app_instance() -> IlinaApp:
    """获取全局 IlinaApp 单例，如果不存在则抛出异常。"""
    app = QApplication.instance()
    if app is None:
        raise RuntimeError("QApplication 尚未初始化")
    # 告诉类型检查器：我知道它是 IlinaApp
    return cast(IlinaApp, app)