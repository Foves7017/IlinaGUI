# 用来放各个配置文件的 TypedDict

from typing import Literal
from pydantic import BaseModel

class WindowConfig(BaseModel):
    """ 窗口配置 """
    edge_board: int = 5  # 用于边界拖动的宽度
    titlebar_height: int = 48  # 标题栏的高度
    window_state: str = ''  # 保存窗口状态
    default_size: tuple[int, int] = (1440, 960)  # 默认窗口尺寸
    scheme_setting: Literal['light', 'dark', 'auto'] = 'auto'
    # default_size: tuple[int, int] = (800, 600)
    chat_width_state: bool = False  # True：展开，False：窄
    chat_splitter_state: str = ''
    chat_hide_tree: bool = False