导入路径：`windows._chat_window.scroll_area.ScrollArea`

# 初始化参数
无
# 属性

| 属性名     | 类型           | 读写  | 说明                                             |
| ------- | ------------ | --- | ---------------------------------------------- |

# 信号

| 信号名    | 参数  | 说明                             |
| ------ | --- | ------------------------------ |

# 方法
```Python
def clear(self):
```
会清空内容
```Python
def add_messages(self, 
		uuids: list[UUID], 
		messages: list[IlinaMessage]
):
```
向区域内添加消息