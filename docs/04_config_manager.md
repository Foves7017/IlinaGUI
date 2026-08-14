# 概述
配置管理器提供了一个设置窗口。需要同时给定一个 JSON 文件名和一个 pydanitc 模型，当用户调节时，可以作为设置窗口使用。
# 用于传递的结构
```Python
class ConfigPage(BaseModel):
	display_name: str  # 显示名称
	filename: str|Path  # 保存的文件名
	save_model: type[BaseModel]  # 保存格式的数据类
```

# 建议的配置格式
配置应该是一个 BaseModel 的子类，并附加了一些规则以用于生成配置界面。
1. 以 `not_in_ui__` 开头的字段不会出现在配置界面中。