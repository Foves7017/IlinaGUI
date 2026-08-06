import sys
from uuid import UUID, uuid4
from pathlib import Path

def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path('.')

def python_runtime_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path('.venv/Scripts/python.exe')

def plugin_dir() -> Path:
    return app_dir()/'plugins'

def config_dir() -> Path:
    return app_dir()/'configs'

def get_short_uuid(uuid: UUID) -> str:
    return str(uuid).split('-')[-1]

NULL_UUID = UUID('00000000-0000-0000-0000-000000000000')

def generate_uuid() -> UUID:
    """ 生成一个 UUID，只保证不等于 NULL_UUID，不保证不重复 """
    res = uuid4()
    while res == NULL_UUID:
        res = uuid4()
    return res
