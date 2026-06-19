# 从 colors.YAML 中导入颜色
# [INFO] 颜色一定要以 _color 结尾！
# [INFO] 颜色一定要以 _color 结尾！
# [INFO] 颜色一定要以 _color 结尾！
# [INFO] 添加颜色的步骤：1. 在 QSS 里写样式。2. 在 dark 和 light 两个 yaml 里指定颜色。3. 更新颜色类
import re
import yaml
import random
import logging
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
from PySide6.QtWidgets import QWidget
from typing import Literal, overload

# --------------------------------------------------------------------

class WindowBaseColors(BaseModel):
    window_background_color: str = '#1f1f1f'
    text_color: str = '#FFFFFF'

    button_hover_color: str = '#333333'
    button_pressed_color: str = '#cccccc'

    close_button_hover_color: str = '#f03e3e'
    close_button_pressed_color: str = '#bd3030'

    title_board_color: str = '#FFFFFF'

class ChatWindowColors(BaseModel):
    role_label_text_color: str = "#DDDDDD"

    input_area_background_color: str = '#252525'
    input_button_color: str = '#303030'
    input_button_hover_color: str = '#303060'
    input_button_pressed_color: str = '#303090'

    role_user_color: str = '#C4A84A'
    role_assistant_color: str = '#7E9BB5'
    role_tool_color: str = '#8AA38D'
    role_system_color: str = '#A8A8A8'
    role_line_color: str = '#FFFFFF'

    float_window_background_color: str = '#000000'
    float_window_background_alpha: int = 128
    float_window_shadow_start_alpha: int = 40

class Colors(BaseModel):
    window_base: WindowBaseColors = Field(default_factory=WindowBaseColors)
    chat_window: ChatWindowColors = Field(default_factory=ChatWindowColors)

# --------------------------------------------------------------------

class ChatWindowConfigs(BaseModel):
    conversion_area_width: int = -1
    max_input_area_height: int = 300
    min_input_area_height: int = 50
    tree_node_radiu: int = 25
    tree_node_space: int = 10
    tree_node_line_width: int = 2
    float_window_radiu: int = 4
    float_window_fixed_width: int = 200
    float_window_fixed_height: int = 150

class WindowBaseConfigs(BaseModel):
    background_images: str|list[str] = []

class Configs(BaseModel):
    chat_window: ChatWindowConfigs = Field(default_factory=ChatWindowConfigs)
    window_base: WindowBaseConfigs = Field(default_factory=WindowBaseConfigs)

# --------------------------------------------------------------------

class QSSFiles(Enum):
    window_base = 'window_base'
    chat_window = 'chat_window'

class QSSInfo(BaseModel):
    model_config = {'arbitrary_types_allowed': True}
    widget: QWidget
    qss_filename: QSSFiles|list[QSSFiles]

type QSSTable = list[QSSInfo]

class QSSFormatter:
    """ 加载 YAML 配置，并提供替换 QSS 占位符的功能 """
    def __init__(self) -> None:
        self.log = logging.getLogger('QSS 注入器')
        self.qss_table: list[QSSInfo] = []
        self.reload('light')
    
    def add_widget(self, widget: QWidget, object_name: str, qss_filename: QSSFiles|list[QSSFiles]):
        """ 向 QSS 注入器里添加组件
        @param widget: QWidget 组件
        @param object_name: 组件的 objectName
        @param qss_filename: QSS 文件名，可以是 QSSFiles 枚举，也可以是 QSSFiles 枚举的列表
        """
        widget.setObjectName(object_name)
        self.qss_table.append(QSSInfo(widget=widget, qss_filename=qss_filename))

    def add_qss_info(self, info: QSSInfo):
        self.qss_table.append(info)

    def delete_qss_infos(self, infos: list[QSSInfo]):
        self.qss_table = list(filter(lambda x: x not in infos, self.qss_table))

    def reload(self, scheme: Literal['light', 'dark']='light') -> None:
        # 读取颜色配置
        color_path = Path(f'./QSS/Colors_{scheme}.yaml')
        self.log.info(f'颜色文件路径：{color_path}')
        try:
            if color_path.exists():
                self.colors: Colors = Colors.model_validate(yaml.safe_load(color_path.read_text(encoding='UTF8')))
        except Exception as e:  # 读取错误什么的
            self.log.error(f'读取颜色文件时发生错误: {e}')
            self.colors: Colors = Colors()
        
        # 读取其他配置
        config_path = Path(f'./QSS/config.yaml')
        try:
            if config_path.exists():
                self.config: Configs = Configs.model_validate(yaml.safe_load(config_path.read_text(encoding='UTF8')))
                # 如果背景是一个列表，就随机选择一个
                if isinstance(self.config.window_base.background_images, list):
                    self.config.window_base.background_images = random.choice(self.config.window_base.background_images)
        except Exception as e:  # 读取错误什么的
            self.log.error(f'读取配置文件时发生错误: {e}')
            self.config: Configs = Configs()

        # 读取并替换 QSS 样式表
        self.sheets: dict[QSSFiles, str] = {}
        for filename in QSSFiles.__members__:
            try:
                # 读取
                with open(f'./QSS/{filename}.qss', 'r', encoding='UTF8') as f:
                    sheet = f.read()
                # 获取对应子类并替换
                color_class: BaseModel = getattr(self.colors, filename)
                for key in type(color_class).model_fields:
                    sheet = sheet.replace('{{' + key + '}}', str(getattr(color_class, key)))
                if hasattr(self.config, filename):
                    config_class: BaseModel = getattr(self.config, filename)
                    for key in type(config_class).model_fields:
                        sheet = sheet.replace('{{' + key + '}}', str(getattr(config_class, key)))
                
                for word in re.findall(r'\{\{.*?\}\}', sheet):
                    self.log.warning(f'未替换的变量 {word}')

                # 缓存
                self.sheets[QSSFiles(filename)] = sheet

            except FileNotFoundError:
                self.log.error(f'找不到 QSS 文件：{filename}')
            except AttributeError:
                self.log.error(f'缺少属性：{filename}')
            except Exception as e:
                self.log.error(f'读取并替换 QSS 文件时发生错误: {e}')

    @overload
    def get_sheet(self, name: QSSFiles) -> str:
        ...

    @overload
    def get_sheet(self, name: list[QSSFiles]) -> str:
        ...

    def get_sheet(self, name) -> str:
        if isinstance(name, list):
            return '\n'.join([self.sheets[name] for name in name])
        else:
            return self.sheets[name]