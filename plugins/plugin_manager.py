import logging 
import importlib
from pathlib import Path

from FovesLog import LoggedTask

from PySide6.QtWidgets import QWidget
from PySide6.QtQuickWidgets import QQuickWidget

from layout.formatter import Formatter
from utils import app_dir

class PluginManager:
    def __init__(self, formatter: Formatter):
        self.log = logging.getLogger('插件管理器')

        # 插件名-内容 Widget 的对应字典
        self.name_to_widget: dict[str, type[QWidget|QQuickWidget]] = {}
        self.name_to_display_name: dict[str, str] = {}
        self.name_to_extra_name: dict[str, list[str]] = {}
        self.name_to_icon_chara: dict[str, str] = {}

        self.formatter = formatter

        # 遍历插件文件夹，导入插件
        with LoggedTask(f'导入插件', logger=self.log) as task:
            for path in (app_dir()/'plugins').iterdir():
                if path.is_dir() and not path.stem.startswith('_'):
                    model = importlib.import_module(path.as_posix().replace('/', '.'))
                    try:               
                        # 加载内容组件         
                        content_widget = getattr(model, 'ContentWidget', None)
                        if content_widget is None:
                            self.log.error(f'插件"{path.stem}"中未找到 ContentWidget, 跳过加载')
                            continue
                        self.name_to_widget[path.stem] = content_widget
                        
                        # 加载显示名称
                        self.name_to_display_name[path.stem] = getattr(model, 'PLUGIN_DISPLAY_NAME', path.stem)

                        # 加载关联的文件格式
                        connect_extname = getattr(model, 'CONNECTED_FILES', None)
                        if connect_extname is not None:
                            if isinstance(connect_extname, str):
                                self.name_to_extra_name[path.stem] = [connect_extname]
                            elif isinstance(connect_extname, list):
                                self.name_to_extra_name[path.stem] = connect_extname
                            else:
                                self.log.warning(f'插件"{path.stem}"中 CONNECTED_FILES 格式错误，忽略')
                        
                        # 加载显示在侧边栏的图标
                        icon = getattr(model, 'ACTIVE_BAR_ICON_CHARA', None)
                        if icon:
                            self.name_to_icon_chara[path.stem] = icon
                            self.log.info(f'发现添加到侧边栏的图标')
                        
                    except ImportError as e:
                        self.log.error(f'插件"{path.stem}"无法导入，已跳过')
                    
                    self.log.info(f'寻找并导入 Yaml')
                    for path, _, files in path.walk():
                        for file in files:
                            if (path/file).suffix == '.yaml':
                                self.formatter.add_yaml(path/file)

                    task.checkpoint(f'已加载"{path.stem}"')
    
    def get_widget_type_by_name(self, name: str) -> type[QWidget|QQuickWidget]|None:
        try:
            return self.name_to_widget[name]
        except KeyError:
            self.log.error(f'未找到名为"{name}"的插件')
            return 
    
    def get_display_name_by_name(self, name: str) -> str:
        return self.name_to_display_name[name]