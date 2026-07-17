from pydantic import BaseModel

from utils import app_dir


CONFIG_PATH = app_dir()/'configs'/'app_config.json'

class AppConfig(BaseModel):
    default_workspace: str = r'D:\\Find-A-Way-VII\\ILINA\WorkPath_II'
    latest_workspace: str|None = None

