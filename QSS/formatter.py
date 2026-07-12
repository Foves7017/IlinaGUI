import re
import yaml
import random
import logging

from pathlib import Path
from FovesLog import LoggedTask
from dataclasses import dataclass

from PySide6.QtWidgets import QWidget

@dataclass
class QSSInfo:
    widget: QWidget
    qssfilename: str|list[str]

class QSSFormatter:
    def __init__(self, qss_path: None|str|Path=None) -> None:
        self.log = logging.getLogger('QSS Formatter')

        if isinstance(qss_path, str):
            self.qss_path: Path = Path(qss_path)
        elif isinstance(qss_path, Path):
            self.qss_path: Path = qss_path
        elif qss_path is None:
            self.qss_path: Path = Path('./qss')
        else:
            raise

        if not (self.qss_path.exists() and self.qss_path.is_dir()):
            raise
        
        self.log.info(f'QSS 文件夹：{str(self.qss_path)}')

        self.yaml: dict[str, dict] = {}
        self.orig_qss: dict[str, str] = {}

        with LoggedTask('加载文件', logger=self.log) as task:
            for path, _, files in self.qss_path.walk():
                for file in files:
                    filename = path / file
                    if filename.suffix == '.qss':
                        with open(filename, 'r', encoding='UTF8') as f:
                            self.orig_qss[file] = f.read()
                    elif filename.suffix == '.yaml':
                        with open(filename, 'r', encoding='UTF8') as f:
                            self.yaml.update(yaml.safe_load(f))

        self.widgets: list[QSSInfo] = []

    def get_yaml(self, scheme: str) -> dict:
        """ 获取 YAML 主题的配置 """
        replace_dict = {}
        if 'general' in self.yaml:
            replace_dict.update(self.yaml['general'])
        if scheme in self.yaml:
            replace_dict.update(self.yaml[scheme])
        return replace_dict

    def format_qss(self, replace_dict: dict) -> dict[str, str]:
        """ 将 YAML 中的配置替换进 QSS """
        formatted_qss: dict[str, str] = {}

        not_found: list[str] = []
        with LoggedTask('将 YAML 中的配置替换进 QSS', logger=self.log) as task:
            for filename in self.orig_qss:
                content = self.orig_qss[filename]
                results = re.findall(r'{{(.*?)}}', self.orig_qss[filename])
                for result in results:
                    try:
                        if isinstance(replace_dict[result], str):
                            content = content.replace("{{"+result+"}}", replace_dict[result])
                        elif isinstance(replace_dict[result], list):
                            content = content.replace("{{"+result+"}}", random.choice(replace_dict[result]))
                        else:
                            content = content.replace("{{"+result+"}}", str(replace_dict[result]))
                    except KeyError:
                        self.log.warning(f'未找到的值：{result}')
                        not_found.append(result)
                formatted_qss[filename] = content
        
        return formatted_qss
    
    def add_widget(self, widget: QWidget, file_name: str|list[str], object_name: str|None=None):
        if object_name is not None:
            widget.setObjectName(object_name)

        self.widgets.append(QSSInfo(widget=widget, qssfilename=file_name))
    
    def set_style(self, formatted_qss: dict[str, str]):
        with LoggedTask('刷新所有组件的样式表', logger=self.log):
            for widget in self.widgets:
                if isinstance(widget.qssfilename, list):
                    style_sheet = '\n\n'.join(formatted_qss[i] for i in widget.qssfilename)
                elif isinstance(widget.qssfilename, str):
                    style_sheet = formatted_qss[widget.qssfilename]
                else:
                    style_sheet = ''

                widget.widget.setStyleSheet(style_sheet)
    
    def reload_from_file(self, scheme: str):
        self.set_style(self.format_qss(self.get_yaml(scheme)))