import re
import yaml
import random
import logging

from FovesLog import LoggedTask
from dataclasses import dataclass

from PySide6.QtQml import QQmlPropertyMap
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget
from PySide6.QtQuickWidgets import QQuickWidget

from utils import app_dir

@dataclass
class QSSInfo:
    widget: QWidget
    qssfilename: str|list[str]

@dataclass
class QMLInfo:
    widget: QQuickWidget
    qmlfilename: str

YAML_FOLDER = app_dir()/'layout'/'yaml'
QSS_FOLDER = app_dir()/'layout'/'qss'
QML_FOLDER = app_dir()/'layout'/'qml'

class Formatter:
    """ 管理 YAML 配置，并实现热重载
    1. YAML 加载功能

    所有的YAML应该遵从如下的格式：
    
    ThemeName:
      Key: value
    
    ThemeName 是 “主题名” 不同文件中相同的主题名会被合并
    Key 是键名，value 值名。
    value 可以是一个列表，在这种情况下，每次访问会随机从其中选取一个。
    当不同文件同一主题的 key 重复时，会自动将 value 合并成列表

    2. QSS 注入功能

    可以在 QSS 中通过 {{key}} 的形式访问在 YAML 中指定的值。在加载时会被替换。

    3. 在 Python 中访问 YAML

    可以通过 getattr 或 getitem 访问值，如果 key 不存在会产生 KeyError

    4. YAML 特殊的主题名
    当主题名为 general 时，无论如何都会被加载

    ---

    热重载：调用 reload 方法
    创建 QWidget：
      1. widget = QWidget()
      2. 调用formatter的add_qss_widget(widget, qss_filename, objname)
    
    创建 QQuickWidget：
      1. widget = QQuickWidget()
      2. 调用formatter的add_qml_widget(widget, qml_filename)
      3. 给 widget 添加后端：widget.rootContext().setContextProperty('backend', backend)

    """
    def __init__(self, theme: str|None=None) -> None:
        self.log = logging.getLogger('Formatter')
        self.qss_cache = {}
        self._theme: str|None = theme 

        self.qss_widgets: list[QSSInfo] = []
        self.qml_widgets: list[QMLInfo] = []

        self.load_yaml()

    def load_yaml(self):
        """ 从 YAML 中加载主题 """
        self.theme_dict = {}  # 保存加载了主题的字典
        with LoggedTask('从 YAML 中加载主题', logger=self.log) as task:
            for path, _, files in YAML_FOLDER.walk():
                for file in files:
                    filename = path / file
                    if filename.suffix == '.yaml':
                        with open(filename, 'r', encoding='UTF8') as f:
                            content = yaml.safe_load(f)
                            for  _theme in [self._theme, 'general']:
                                if _theme in content:
                                    for key in content[_theme]:
                                        if key in self.theme_dict:
                                            match isinstance(self.theme_dict[key], list), isinstance(content[_theme][key], list):
                                                case False, False:
                                                    self.theme_dict[key] = [self.theme_dict[key], content[_theme][key]]
                                                case False, True:
                                                    self.theme_dict[key] = [self.theme_dict[key]] + content[_theme][key]
                                                case True, False:
                                                    self.theme_dict[key] = self.theme_dict[key] + [content[_theme][key]]
                                                case True, True:
                                                    self.theme_dict[key] = self.theme_dict[key] + content[_theme][key]
                                        else:
                                            self.theme_dict[key] = content[_theme][key]
                        task.checkpoint(f'已加载 {str(filename)}')

    def __getattr__(self, name):
        if name in self.theme_dict:
            if isinstance(self.theme_dict[name], list):
                return random.choice(self.theme_dict[name])
            else:
                return self.theme_dict[name]
        else:
            raise KeyError(f'{name} 当前主题的 YAML 文件中不包含 {name}')
    
    def __getitem__(self, key):
        return self.__getattr__(key)

    def load_qss(self, filepath: str) -> str:
        """ 从文件加载 QSS，会返回已经替换的 QSS """
        if filepath in self.qss_cache:
            return self.qss_cache[filepath]
        else:
            with LoggedTask(f'加载 {filepath}', logger=self.log):
                with open(filepath, 'r', encoding='UTF8') as f:
                    content = f.read()
                    results = re.findall(r'{{(.*?)}}', content)
                    for result in results:
                        try:
                            content = content.replace("{{"+result+"}}", str(self[result]))
                        except KeyError as e:
                            self.log.warning(repr(e))
            self.qss_cache[filepath] = content
            return content

    @property
    def theme(self):
        return self._theme
    
    @theme.setter
    def theme(self, new_value: str):
        self._theme = new_value
        self.reload()

    
    def add_qss_widget(self, qwidget: QWidget, file_name: str|list[str], object_name: str|None=None):
        """ 设置一个关联到 QSS 的组件，可以同时快速设置 object_name """
        if object_name is not None:
            qwidget.setObjectName(object_name)

        self.qss_widgets.append(QSSInfo(widget=qwidget, qssfilename=file_name))
    
    def add_qml_widget(self, qqwidget: QQuickWidget, filename: str):
        """ 设置一个关联到 QML 的组件 """
        self.qml_widgets.append(QMLInfo(widget=qqwidget, qmlfilename=filename))
    
    def set_qss_style(self):
        count = 0
        with LoggedTask('刷新所有QSS组件的样式表', logger=self.log):
            for widget in self.qss_widgets:
                if isinstance(widget.qssfilename, list):
                    style_sheet = '\n\n'.join(self.load_qss(i) for i in widget.qssfilename)
                elif isinstance(widget.qssfilename, str):
                    style_sheet = self.load_qss(widget.qssfilename)
                else:
                    style_sheet = ''

                widget.widget.setStyleSheet(style_sheet)
                count += 1
            self.log.info(f'刷新了 {count} 个QSS组件')
    
    def set_qml_style(self):
        self.qmlmap = QQmlPropertyMap()
        for key in self.theme_dict.keys():
            self.qmlmap.insert(key, self[key])
        count = 0
        with LoggedTask('刷新所有QML组件的样式', logger=self.log):
            for widget in self.qml_widgets:
                widget.widget.engine().clearComponentCache()
                widget.widget.rootContext().setContextProperty('formatter', self.qmlmap)
                widget.widget.setSource(QUrl.fromLocalFile(widget.qmlfilename))
                count += 1
            self.log.info(f'刷新了 {count} 个QML组件')

    def reload(self):
        self.qss_cache = {}
        self.load_yaml()
        self.set_qss_style()
        self.set_qml_style()