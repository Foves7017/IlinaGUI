# =====================================================================
#  color_loader.py  —  QSS 颜色与配置加载器
# =====================================================================
# [说明] 颜色一定要以 _color 结尾！
# [说明] 颜色一定要以 _color 结尾！
# [说明] 颜色一定要以 _color 结尾！
# [说明] 添加颜色的步骤：
#        1. 在 QSS 里写样式。
#        2. 在 dark 和 light 两个 yaml 里指定颜色。
#        3. 更新本文件中的颜色类。
# [同步] 本文件的默认值应与 Colors_dark.yaml / Colors_light.yaml 保持同步。
# =====================================================================

import re
import yaml
import random
import logging
from enum import Enum
from pydantic import BaseModel, Field
from PySide6.QtWidgets import QWidget
from typing import Literal, overload
from IlinaEngine.type import IlinaMessageRoles

from utils import app_dir

# ----------------- 窗口的基本设置 ----------------------------------------
# 对应 YAML 中 window_base 节点
class WindowBaseColors(BaseModel):
    window_background_color: str = 'rgba(64, 64, 64, 255)'          # 窗口背景色
    background_filter_color: str = 'rgba(0, 0, 0, 192)'             # 背景滤镜色（模态框遮罩）
    default_text_color: str = 'rgba(255, 255, 255, 255)'                    # 默认文字颜色
    titlebar_button_hover_color: str = 'rgba(255, 255, 255, 64)'             # 普通按钮悬停色
    titlebar_button_pressed_color: str = 'rgba(255, 255, 255, 128)'          # 普通按钮按下的颜色

    close_button_hover_color: str = 'rgba(240, 62, 62, 255)'        # 关闭按钮悬停色
    close_button_pressed_color: str = 'rgba(189, 48, 48, 255)'      # 关闭按钮按下的颜色


# ----------------- 对话窗口设置 ------------------------------------------
# 对应 YAML 中 chat_window 节点
class ChatWindowColors(BaseModel):
    general_split_line_color: str = 'rgba(255, 255, 255, 192)'      # 全局分割线颜色

    input_area_backgournd_color: str = 'rgba(255, 255, 255, 64)'    # 输入框背景颜色
    input_area_boarder_color: str = 'rgba(255, 255, 255, 255)'      # 输入框边框颜色
    input_button_background_color: str = 'rgba(255, 255, 255, 64)'  # 按钮背景颜色
    input_button_boarder_color: str = 'rgba(255, 255, 255, 0)'      # 按钮边框颜色
    input_button_hover_background_color: str = 'rgba(50, 50, 100, 128)'            # 发送按钮悬停颜色
    input_button_pressed_background_color: str = 'rgba(50, 50, 100, 255)'           # 发送按钮按下颜色
    conversion_item_editing_background_color: str = 'rgba(255, 255, 255, 64)'  # 对话条目编辑背景色
    conversion_item_reasoning_content_color: str = "#DDDDDD"    # 对话条目思考文字颜色

    role_user_normal_color: str = '#FFFF80'                           # 用户角色浅色
    role_assistant_normal_color: str = '#8080ff'                      # 助手角色浅色
    role_tool_normal_color: str = '#80FF80'                           # 工具角色浅色
    role_system_normal_color: str = '#808080'                         # 系统角色浅色
    role_error_normal_color: str = '#FF8080'                          # 错误角色浅色

    role_user_extra_color: str = '#808040'                            # 用户角色深色
    role_assistant_extra_color: str = '#404080'                       # 助手角色深色
    role_tool_extra_color: str = '#408040'                            # 工具角色深色
    role_system_extra_color: str = '#808080'                          # 系统角色深色
    role_error_extra_color: str = '#804040'                           # 错误角色深色

    tree_line_color: str = '#404040'

    state_label_background_color: str = 'rgba(255, 255, 255, 64)'     # 状态标签背景色
    state_label_hover_color: str = 'rgba(255, 255, 255, 128)'         # 状态标签悬停色
    state_idle_color: str = '#FFF'                                     # IDLE 状态颜色
    state_transport_color: str = '#AFA'                                # TRANSPORTING 状态颜色
    state_connect_color: str = '#FFA'                                  # CONNECTING 状态颜色

    conversion_item_button_hover_color: str = 'rgba(240, 240, 255, 64)'       # 对话条目按钮悬停色
    conversion_item_button_pressed_color: str = 'rgba(240, 240, 255, 128)'    # 对话条目按钮按下色

    title_edit_background_color: str = 'rgba(240, 240, 255, 64)'

    work_path_color: str = "rgba(240, 240, 255, 64)"

    float_window_background_color: str = '#000000'                   # 浮动窗口背景色
    float_window_background_alpha: int = 128                         # 浮动窗口背景透明度 (0-255)
    float_window_shadow_start_alpha: int = 40                        # 浮动窗口阴影起始透明度
    float_window_split_color: str = 'rgba(240, 240, 255, 128)'
    float_window_button_text_color: str = 'rgba(240, 240, 255, 1)'
    float_window_button_hover_color: str = 'rgba(240, 240, 255, 64)'
    float_window_button_pressed_color: str = 'rgba(240, 240, 255, 128)'


class Colors(BaseModel):
    window_base: WindowBaseColors = Field(default_factory=WindowBaseColors)
    chat_window: ChatWindowColors = Field(default_factory=ChatWindowColors)

# --------------------------------------------------------------------
#  以下为配置类与 QSS 注入逻辑，通常不需要频繁修改
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
    background_images: str|list[str]|None = []

class Configs(BaseModel):
    chat_window: ChatWindowConfigs = Field(default_factory=ChatWindowConfigs)
    window_base: WindowBaseConfigs = Field(default_factory=WindowBaseConfigs)

# --------------------------------------------------------------------

class QSSFiles(str, Enum):
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
        color_path = app_dir() / 'QSS' / f'Colors_{scheme}.yaml'
        self.log.info(f'颜色文件路径：{color_path}')
        try:
            if color_path.exists():
                self.colors: Colors = Colors.model_validate(yaml.safe_load(color_path.read_text(encoding='UTF8')))
        except Exception as e:  # 读取错误什么的
            self.log.error(f'读取颜色文件时发生错误: {e}')
            self.colors: Colors = Colors()
        
        # 读取其他配置
        config_path = app_dir() / 'QSS' / f'config.yaml'
        try:
            if config_path.exists():
                self.config: Configs = Configs.model_validate(yaml.safe_load(config_path.read_text(encoding='UTF8')))
                # 如果背景是一个列表，就随机选择一个
                if self.config.window_base.background_images is None:
                    self.config.window_base.background_images = ''
                elif isinstance(self.config.window_base.background_images, list):
                    self.config.window_base.background_images = random.choice(self.config.window_base.background_images)
        except Exception as e:  # 读取错误什么的
            self.log.error(f'读取配置文件时发生错误: {e}')
            self.config: Configs = Configs()

        # 读取并替换 QSS 样式表
        self.sheets: dict[QSSFiles, str] = {}
        for filename in QSSFiles.__members__:
            try:
                # 读取
                with open(app_dir()/'QSS'/f'{filename}.qss', 'r', encoding='UTF8') as f:
                    sheet = f.read()    

                # 获取对应子类并替换
                if hasattr(self.colors, filename):
                    color_class: BaseModel = getattr(self.colors, filename)
                    for key in type(color_class).model_fields:
                        sheet = sheet.replace('{{' + key + '}}', str(getattr(color_class, key)))
                        
                if hasattr(self.config, filename):
                    config_class: BaseModel = getattr(self.config, filename)
                    for key in type(config_class).model_fields:
                        sheet = sheet.replace('{{' + key + '}}', str(getattr(config_class, key)))
                
                for word in re.findall(r'\{\{.*?\}\}', sheet):
                    self.log.warning(f'{filename} 中未替换的变量 {word}')

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
    
    def get_role_color(self, role: IlinaMessageRoles, is_extra: bool = False):
        suffix = 'extra_color' if is_extra else 'normal_color'
        return getattr(self.colors.chat_window, f'role_{role}_{suffix}')
