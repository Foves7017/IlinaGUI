import re
import yaml
import random
import logging

from pathlib import Path
from FovesLog import LoggedTask
from dataclasses import dataclass

from PySide6.QtCore import QObject, QUrl, Slot, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtQuickWidgets import QQuickWidget

@dataclass
class QSSInfo:
    widget: QWidget
    qssfilename: list[Path]
    object_name: str

    @classmethod
    def format(cls, widget: QWidget, file_name: str|list[str]|Path|list[Path], object_name: str) -> 'QSSInfo':
        if isinstance(file_name, list):
            file_name = [Path(line) for line in file_name]
        else:
            file_name = [Path(file_name)]
        widget.setObjectName(object_name)
        return cls(widget, file_name, object_name)

@dataclass
class QMLInfo:
    widget: QQuickWidget
    qmlfilename: Path
    object_name: str

    @classmethod
    def format(cls, widget: QQuickWidget, file_name: str|Path, object_name: str) -> 'QMLInfo':
        if isinstance(file_name, str):
            file_name = Path(file_name)
        widget.setObjectName(object_name)
        return cls(widget, file_name, object_name)


class ThemeBridge(QObject):
    """将 YAML 主题字典桥接到 QML。

    在 Formatter 初始化时立即创建，add_qml_widget 时注入到 QML context。
    reload 时通过 update() 刷新内部数据，不重建对象，保证 QML 中 formatter 永不为 null。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dict: dict = {}

    def update(self, theme_dict: dict):
        """用最新的 theme_dict 刷新内部缓存（列表值随机选取固化）"""
        self._dict.clear()
        for key, value in theme_dict.items():
            if isinstance(value, list):
                self._dict[key] = random.choice(value)
            else:
                self._dict[key] = value

    @Slot(str, result='QVariant')
    def get(self, key: str):
        return self._dict.get(key)

class ThemeManager(QObject):
    """ 管理 YAML 配置，并实现热重载
    1. YAML 加载功能

    所有的YAML应该遵从如下的格式：
    
    ThemeName:
      Key: value
    
    ThemeName 是 "主题名" 不同文件中相同的主题名会被合并
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

    ---

    创建 QWidget：
      1. widget = QWidget()
      2. 调用formatter的add_qss_widget(widget, qss_filename, objname)
    
    创建 QQuickWidget：
      1. widget = QQuickWidget()
      2. 调用formatter的add_qml_widget(widget, qml_filename)
      3. 给 widget 添加后端：widget.rootContext().setContextProperty('backend', backend)

    """
    theme_reloaded = Signal()

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.log = logging.getLogger('主题管理器')
        self._theme: str|None = None

        self.qss_widgets: dict[str, QSSInfo] = {}
        self.qml_widgets: dict[str, QMLInfo] = {}
        self.yamls: list[Path] = []
        
        self.qss_cache = {}
        self.theme_dict = {}  # 保存加载了主题的字典

        # 提前创建 ThemeBridge，保证 add_qml_widget 时就能注入
        self.qmlmap = ThemeBridge()

        # 正在重载的标志
        self.reloading: bool = False

    def add_yaml(self, filename: str|Path):
        self.yamls.append(Path(filename))
        self.log.info(f'添加了 YAML 文件：{filename}')

    def add_qss_widget(self, qwidget: QWidget, file_name: str|list[str]|Path|list[Path], object_name: str):
        """ 设置一个关联到 QSS 的组件，会自动设置 objectName """
        info = QSSInfo.format(widget=qwidget, file_name=file_name, object_name=object_name)
        self.qss_widgets[object_name] = info
        self.log.info(f'添加了 QSS 组件 {qwidget.objectName()} - {file_name}')
    
    def add_qml_widget(self, qqwidget: QQuickWidget, file_name: str|Path, object_name: str):
        """ 设置一个关联到 QML 的组件，会自动设置 objectName """
        info = QMLInfo.format(widget=qqwidget, file_name=file_name, object_name=object_name)
        self.qml_widgets[object_name] = info
        self.log.info(f'添加了 QML 组件 {qqwidget.objectName()} {file_name}')

    def load_yaml(self, filename: Path):
        """ 加载 YAML 文件 """
        self.log.debug(f'加载 YAML 文件 {filename}')
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
                            self.log.debug(f'覆盖 {key} 为 {self.theme_dict[key]}')
                        else:
                            self.theme_dict[key] = content[_theme][key]
                            self.log.debug(f'添加 {key} 为 {self.theme_dict[key]}')

    def load_qss(self, info: QSSInfo):
        """ 从文件加载 QSS """
        style_sheet = ''
        for filename in info.qssfilename:
            if filename in self.qss_cache:
                style_sheet += self.qss_cache[filename] + '\n\n'
            else:
                content = filename.read_text('UTF8')
                results = re.findall(r'{{(.*?)}}', content)
                for result in results:
                    try:
                        content = content.replace("{{"+result+"}}", str(self[result]))
                    except KeyError as e:
                        self.log.warning(repr(e))
                self.qss_cache[filename] = content
                style_sheet += content + '\n\n'

        info.widget.setStyleSheet(style_sheet)

    def load_qml(self, info: QMLInfo):
        """ 设置一个关联到 QML 的组件，并立即注入 formatter """
        # 立刻设置 context property，保证后续 QML 加载时 formatter 不会为 null
        info.widget.engine().clearComponentCache()
        info.widget.rootContext().setContextProperty('formatter', self.qmlmap)
        info.widget.setSource(QUrl.fromLocalFile(info.qmlfilename.as_posix()))

    def __getattr__(self, name):
        self.log.debug(f'访问属性：{name}')
        if name in self.theme_dict:
            if isinstance(self.theme_dict[name], list):
                return random.choice(self.theme_dict[name])
            else:
                return self.theme_dict[name]
        else:
            raise KeyError(f'当前主题的 YAML 文件中不包含 {name}')

    def __getitem__(self, key):
        return self.__getattr__(key)

    @property
    def theme(self):
        return self._theme
    
    @theme.setter
    def theme(self, new_value: str):
        self._theme = new_value
        self.reload()

    def reload_yaml(self, theme_name: str|None=None, filenames:list[str|Path]|None=None):
        # 清空 QSS 缓存
        self.qss_cache = {}

        yamls = [Path(name) for name in filenames] if filenames else self.yamls
        with LoggedTask('重载 YAML', self.log) as task:
            if theme_name is not None:
                self._theme = theme_name
            self.log.info(f'当前主题为 {theme_name}')

            self.theme_dict = {}
            self.log.debug(f'本次更新的 YAML: {yamls}')
            for file in yamls:
                try:
                    self.load_yaml(file)
                except Exception as e:
                    from traceback import format_tb
                    self.log.error(f'在加载 YAML 文件时出现错误：{e}\n{'\n'.join(format_tb(e.__traceback__))}')
            task.checkpoint('重载 YAML 文件')

            for key, value in self.theme_dict.items():
                if isinstance(value, list):
                    self.theme_dict[key] = random.choice(value)
            task.checkpoint('固定列表')

    def reload_qss(self, object_names: list[str]|None=None):
        with LoggedTask('重载 QSS', self.log) as task:
            if object_names:
                qsss = [self.qss_widgets[name] for name in object_names if name in self.qss_widgets]
            else:
                qsss = self.qss_widgets.values()
            self.log.debug(f'本次更新的 QSS 组件: {[qss.object_name for qss in qsss]}')

            delete_list: list[QSSInfo] = []

            count = 0
            for info in qsss:
                try:
                    self.load_qss(info)
                except RuntimeError:
                    delete_list.append(info)
                count += 1
            task.checkpoint(f'刷新了 {count} 个 QSS 组件')

            if len(delete_list) > 0:
                for info in delete_list:
                    del self.qss_widgets[info.object_name]
                task.checkpoint(f'删除了 {len(delete_list)} 个失效的 QSS 组件')

    def reload_qml(self, object_names: list[str]|None=None):
        with LoggedTask('重载 QML', self.log) as task:
            if object_names:
                qmls = [self.qml_widgets[name] for name in object_names if name in self.qml_widgets]
            else:
                qmls = self.qml_widgets.values()

            self.log.debug(f'本次更新的 QML 组件: {[qss.object_name for qss in qmls]}')
        
            self.qmlmap.update(self.theme_dict)

            delete_list: list[QMLInfo] = []

            count = 0
            for info in qmls:
                try:
                    self.load_qml(info)
                except RuntimeError:
                    delete_list.append(info)
                count += 1
            task.checkpoint(f'刷新了 {count} 个 QML 组件')

            if len(delete_list) > 0:
                for info in delete_list:
                    del self.qml_widgets[info.object_name]
                task.checkpoint(f'删除了 {len(delete_list)} 个失效的 QML 组件')

    def reload(self, theme_name: str|None=None):
        self.reloading = True
        self.reload_yaml(theme_name)
        self.reload_qss()
        self.reload_qml()
        self.theme_reloaded.emit()
        self.reloading = False