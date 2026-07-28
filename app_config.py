from pydantic import BaseModel

from utils import config_dir


APP_CONFIG_PATH = config_dir()/'app_config.json'

class AppConfig(BaseModel):
    default_workspace: str = r'D:\\Find-A-Way-VII\\ILINA\WorkPath_II'
    latest_workspace: str|None = None
    light_theme_name: str = 'light'
    dark_theme_name: str = 'dark'