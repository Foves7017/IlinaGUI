from pathlib import Path
from typing import Type

from pydantic import BaseModel

class SettingItem(BaseModel):
    name: str
    config_filepath: str|Path
    config_model: Type[BaseModel]