import sys
from uuid import UUID
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict
from FovesConfig import ConfigLoader
from PySide6.QtWidgets import QWidget
from PySide6.QtQuickWidgets import QQuickWidget


def app_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path('.')

def python_runtime_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path('.venv/Scripts/python.exe')

def plugin_path() -> Path:
    return app_path()/'plugins'

def config_path() -> Path:
    return app_path()/'configs'

APP_CONFIG_PATH = config_path()/'app_config.json'

class AppConfig(BaseModel):
    default_workspace: str = Field(
        default='', 
        title='默认工作目录',
        description='当 Ilina GUI 未带参数启动时，默认打开的工作目录'
    )
    light_theme_name: str = Field(default='Ilina_light', title='亮色主题名称')
    dark_theme_name: str = Field(default='Ilina_dark', title='暗色主题名称')
    not_in_ui__latest_workspace: str|None = Field(default=None)
    not_in_ui__main_window_state_: str = Field(default='')

def workspace_path() -> Path:
    """ 获取工作目录 """
    config = ConfigLoader(APP_CONFIG_PATH, AppConfig).readonly()
    workspace: Path = Path(config.not_in_ui__latest_workspace or config.default_workspace)
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.is_dir():
            workspace = path
        elif path.is_file():
            workspace = path.parent
    return workspace

class ConfigPage(BaseModel):
    name: str
    config_filepath: str|Path
    config_model: type[BaseModel]

class DockInfo(BaseModel):
    """ 存储一个 Dock 的相关信息 """
    # 信息
    plugin_display_name: str  # 插件的显示名称
    plugin_name: str  # 所属的插件名
    uuid: UUID  

    # 参数
    openfile: Path|None  # 传入的文件，None 表示从活动栏启动

class PluginInfo(BaseModel):
    """ 描述一个插件的内容 """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = ''
    display_name: str = ''
    dock_widget: type[QQuickWidget|QWidget]|None = None
    active_bar_chara: str|None = None
    config_model: ConfigPage|None = None