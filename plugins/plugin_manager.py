import logging 
import importlib
from typing import Callable

from FovesLog import LoggedTask

from PySide6.QtWidgets import QWidget
from PySide6.QtQuickWidgets import QQuickWidget

from utils import app_dir, python_runtime_path
from theme_manager import get_theme_manager
from .consts import SettingItem

class PluginManager:
    def __init__(self):
        self.log = logging.getLogger('插件管理器')

        # 插件名-内容 Widget 的对应字典
        self.name_to_widget: dict[str, type[QWidget|QQuickWidget]] = {}
        self.name_to_display_name: dict[str, str] = {}
        self.name_to_extra_name: dict[str, list[str]] = {}
        self.name_to_icon_chara: dict[str, str] = {}
        self.name_to_icon_hook: dict[str, Callable] = {}
        self.settings: list[SettingItem] = []

        # 遍历插件文件夹，导入插件
        with LoggedTask(f'导入插件', logger=self.log) as task:
            count = 0
            for path in (app_dir()/'plugins').iterdir():
                if path.is_dir() and not path.stem.startswith('_'):
                    plugin_name = path.stem
                    self.log.info(f'开始导入 {plugin_name}')

                    try:
                        model = importlib.import_module(path.as_posix().replace('/', '.'))
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
                        model = importlib.import_module(path.as_posix().replace('/', '.'))
                    try:               
                        # 加载内容组件         
                        content_widget = getattr(model, 'ContentWidget', None)
                        if content_widget:
                            self.log.info(f'插件"{plugin_name}"中发现 ContentWidget')
                            self.name_to_widget[plugin_name] = content_widget
                        
                        # 加载显示名称
                        self.name_to_display_name[plugin_name] = getattr(model, 'PLUGIN_DISPLAY_NAME', plugin_name)

                        # 加载关联的文件格式
                        connect_extname = getattr(model, 'CONNECTED_FILES', None)
                        if connect_extname is not None:
                            if isinstance(connect_extname, str):
                                self.name_to_extra_name[plugin_name] = [connect_extname]
                            elif isinstance(connect_extname, list):
                                self.name_to_extra_name[plugin_name] = connect_extname
                            else:
                                self.log.warning(f'插件"{plugin_name}"中 CONNECTED_FILES 格式错误，忽略')
                        
                        # 加载显示在侧边栏的图标
                        icon = getattr(model, 'ACTIVE_BAR_ICON_CHARA', None)
                        if icon:
                            self.name_to_icon_chara[plugin_name] = icon
                            self.log.info(f'发现添加到侧边栏的图标')
                            
                        # 加载侧边栏创建钩子
                        hook = getattr(model, 'ACTIVE_BAR_CLICK_HOOK', None)
                        if hook:
                            self.name_to_icon_hook[plugin_name] = hook
                            self.log.info(f'发现侧边栏按钮点击钩子')

                        # 加载设置项目
                        settings: list[SettingItem] = getattr(model, 'SETTINGS', [])
                        if len(settings) > 0:
                            self.settings.extend(settings)
                            self.log.info(f'添加了以下配置面板：{', '.join([x.name for x in settings])}')

                    except ImportError as e:
                        self.log.error(f'插件"{plugin_name}"无法导入，已跳过')
                    
                    self.log.info(f'寻找并导入 Yaml')
                    for path, _, files in path.walk():
                        for file in files:
                            if (path/file).suffix == '.yaml':
                                get_theme_manager().add_yaml(path/file)

                    task.checkpoint(f'已加载"{plugin_name}"')
                    count += 1

            self.log.info(f'加载了 {count} 个插件')   
    
    def get_widget_type_by_name(self, name: str) -> type[QWidget|QQuickWidget]|None:
        try:
            return self.name_to_widget[name]
        except KeyError:
            self.log.error(f'未找到名为"{name}"的插件')
            return 
    
    def get_display_name_by_name(self, name: str) -> str:
        return self.name_to_display_name[name]

manager: PluginManager|None = None

def get_plugin_manager() -> PluginManager:
    global manager
    if manager is None:
        manager = PluginManager()
    return manager