from uuid import UUID
from utils import app_dir, config_dir
from pydantic import BaseModel
from pydantic import Field
# from pydantic import BaseModel, Field  # <- 会报错
# 要维护代码，你需要遵守如下的规则：
# 第一：不要在 manager/consts.py（这里） 中同时导入 BaseModel 和 Field，但其他地方没有问题。
# 第二：如果需要使用 Field，必须先单独导入 BaseModel，就如同当前代码显示的那样。
# 第三：不要尝试解释为什么。
# 第四：如果你违反规则一，错误只会发生在这里，不会发生在项目其他任何地方。
# 第五：人格启动
# 第六：如果你发现它突然正常了，不要删除这个分开的 import。因为它只是暂时允许你通过。
# 
# 具体而言，如果写在一起，报错如下：
#
# 发生异常: ImportError
# cannot import name 'import_string' from partially initialized module 'pydantic._internal._validators' (most likely due to a circular import) (d:\Find-A-Way-VII\IlinaGUI\.venv\Lib\site-packages\pydantic\_internal\_validators.py)
#   File "D:\Find-A-Way-VII\IlinaGUI\manager\consts.py", line 5, in <module>
#     from pydantic import BaseModel, Field
#     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "D:\Find-A-Way-VII\IlinaGUI\manager\manager.py", line 11, in <module>
#     from .consts import *
#   File "D:\Find-A-Way-VII\IlinaGUI\IlinaGUI.py", line 12, in <module>
#     from manager.manager import Manager
# ImportError: cannot import name 'import_string' from partially initialized module 'pydantic._internal._validators' (most likely due to a circular import) (d:\Find-A-Way-VII\IlinaGUI\.venv\Lib\site-packages\pydantic\_internal\_validators.py)
# 
# 我也不知道为什么分开这两行就好了，要是你未来知道了，一定要写在这里。

ACTIVEBAR_QML_PATH = str(app_dir()/'manager'/'active_bar.qml')
DOCK_MANAGER_QSS_PATH = str(app_dir()/'manager'/'dock_manager.qss')
MANAGER_YAML_PATH = str(app_dir()/'manager'/'manager_window.yaml')

MANAGER_CONFIG_PATH = config_dir()/'manager_window.json'

class DockInfo(BaseModel):
    plugin_name: str
    uuid: UUID
    openfile: str|None

class ManagerConfig(BaseModel):
    dock_state: str = ''
    # created_docks: dict[UUID, str] = {}
    created_docks: list[DockInfo] = Field(default_factory=list)
