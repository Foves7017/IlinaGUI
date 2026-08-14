import time
import logging
import importlib
from pathlib import Path
from traceback import format_tb

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from FovesLog import LoggedTask

from globals import plugin_path, python_runtime_path, PluginInfo

class PluginManager(QObject):
    start_load_plugin = Signal(str)
    all_plugin_loaded = Signal()
    def __init__(self, parent):
        super().__init__(parent)
        self.log = logging.getLogger('插件管理器')
        self.plugins: dict[str, PluginInfo] = {}
        self.loaded: bool = False  # 检测是否加载完成

    def load_plugin(self):
        # 遍历插件文件夹，导入插件
        with LoggedTask(f'导入插件', logger=self.log) as task:
            count = 0
            for path in plugin_path().iterdir():
                if path.is_dir() and not path.stem.startswith('_'):

                    
                    info = PluginInfo(name=path.stem)
                    self.log.info(f'开始导入 {info.name}')
                    self.start_load_plugin.emit(info.name)

                    # self.log.warning(f'调试延时：1 秒')
                    # time.sleep(1)

                    try:
                        module = importlib.import_module(path.as_posix().replace('/', '.'))
                    except ImportError:
                        # 检测并安装依赖
                        req_list = path/'requirements.txt'
                        if req_list.exists():
                            self.log.info(f'发现依赖列表，开始安装')
                            import subprocess
                            cmd = [python_runtime_path(), '-m', 'pip', 'install', '-r', req_list.as_posix()]
                            try:
                                subprocess.run(cmd, check=True, capture_output=True, text=True)
                                self.log.info(f"成功安装")
                            except subprocess.CalledProcessError as e:
                                self.log.error(f"安装失败：{e.stderr}，跳过导入")
                                continue
                        module = importlib.import_module(path.as_posix().replace('/', '.'))

                    try:
                        # THEME_YAML
                        yamls = getattr(module, 'THEME_YAML', None)
                        try:
                            if isinstance(yamls, Path):
                                self.log.info(f'发现主题 YAML 文件，正在添加')
                                # 当然了，这里要是换成 app_instance 会造成循环导入
                                QApplication.instance().theme_manager.add_yaml(yamls) # type: ignore
                            elif isinstance(yamls, list) and isinstance(yamls[0], Path):
                                self.log.info(f'发现主题 YAML 文件，正在添加')
                                for yaml in yamls:
                                    # 这里也是
                                    QApplication.instance().theme_manager.add_yaml(yaml) # type: ignore
                        except Exception as e:
                            self.log.error(f'在导入 YAML 时遇到错误：{repr(e)}\n{format_tb(e.__traceback__)}')

                        try:
                            # PLUGIN_DISPLAY_NAME
                            info.display_name = getattr(module, 'DISPLAY_NAME', info.name)
                            if info.display_name != info.name:
                                self.log.info(f'发现显示名称：{info.display_name}')
                        except Exception as e:
                            self.log.error(f'在导入 DISPLAY_NAME 时遇到错误：{repr(e)}\n{format_tb(e.__traceback__)}')

                        try:
                            # DOCK_WIDGET
                            info.dock_widget = getattr(module, 'DOCK_WIDGET', None)
                            if info.dock_widget:
                                self.log.info(f'发现 DOCK_WIDGET，正在添加')
                                # ACTIVE_BAR_ICON_CHARA
                                info.active_bar_chara = getattr(module, 'ACTIVE_BAR_ICON_CHARA', None)
                                if info.active_bar_chara:
                                    self.log.info(f'发现 ACTIVE_BAR_ICON_CHARA：chr({ord(info.active_bar_chara)})')
                        except Exception as e:
                            self.log.error(f'在导入 DOCK_WIDGET 时遇到错误：{repr(e)}\n{format_tb(e.__traceback__)}')

                        try:
                            # CONFIG_MODEL
                            info.config_model = getattr(module, 'CONFIG_MODEL', None)
                            if info.config_model:
                                self.log.info(f'发现 CONFIG_MODEL，正在添加')
                        except Exception as e:
                            self.log.error(f'在导入 CONFIG_MODEL 时遇到错误：{repr(e)}\n{format_tb(e.__traceback__)}')

                    except ImportError as e:
                        self.log.error(f'插件"{info.name}"无法导入，已跳过')
                        continue

                    self.plugins[info.name] = info
                    count += 1

        self.log.info(f'加载了 {count} 个插件')
        self.all_plugin_loaded.emit()
        self.loaded = True
