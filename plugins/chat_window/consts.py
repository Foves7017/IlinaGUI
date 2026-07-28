from pydantic import BaseModel

from utils import app_dir

CONFIG_PATH = app_dir()/'configs'/'window.json'
QSS_FILEPATH = r'plugins\chat_window\chat_window.qss'

class ChatWindowConfig(BaseModel):
    chat_splitter_state: str = ''
    scroll_speed: int = 100  # 滚动速度
    max_collapse_height: int = 100  # 折叠高度