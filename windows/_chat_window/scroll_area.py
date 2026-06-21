import logging
from uuid import UUID
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy
from PySide6.QtCore import Qt, Signal
from IlinaEngine import IlinaMessage

from .conversion_item import ConversionItem
from QSS import QSSFiles, qss_formatter

class ScrollArea(QScrollArea):
    start_edit_node = Signal(UUID)
    edit_finished = Signal(UUID, IlinaMessage, bool)  # 编辑完成的信号
    invoke_from_node = Signal(UUID)

    def __init__(self):
        super().__init__()
        self.log = logging.getLogger('滚动区域')
        qss_formatter.add_widget(self, 'ScrollArea', QSSFiles.chat_window)

        self.setWidgetResizable(True)  # 内容 widget 随滚动区域自适应宽度
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 滚动区域内部的内容容器
        self.content = self._new_content()
        self.setWidget(self.content)

        # UUID 到 Item 的记录表
        self.uuid_to_conversion_item: dict[UUID, ConversionItem] = {}
        self.last_item: UUID   # 最下面的节点
    
    def scroll_to_node(self, target: UUID):
        """ 滚动到指定节点 """
        try:
            item = self.uuid_to_conversion_item[target]
            # print(f'Item 下边界：{item.geometry().bottom()} 上边界：{item.geometry().top()}')
            self.ensureWidgetVisible(item)
            # # 如果item底部在屏幕外，就滚动上去
            # if item.geometry().bottom() > self.verticalScrollBar().value():
            #     self.verticalScrollBar().setValue(item.geometry().bottom())
        except KeyError:
            pass
    
    def wheelEvent(self, arg__1: QWheelEvent) -> None:
        return super().wheelEvent(arg__1)
            
    def update_item(self, uuid: UUID, new_message: IlinaMessage):
        """ 更新节点 """
        item = self.uuid_to_conversion_item[uuid]
        item.update_message(new_message)

    def add_messages(self, uuids: list[UUID], messages: list[IlinaMessage]):
        """ 向区域内添加节点 """
        for uuid, message in zip(uuids, messages):
            self.log.info(f'添加节点：{uuid}')
            new_item = ConversionItem(uuid, message)
            self.content_layout.addWidget(new_item)  # 添加到布局
            self.uuid_to_conversion_item[uuid] = new_item  # 添加到查找表
            new_item.edit_node.connect(self.start_edit_node.emit)
            new_item.edit_finished.connect(self.edit_finished.emit)
            new_item.invoke_from_node.connect(self.invoke_from_node.emit)
            self.last_item = uuid

    def clear(self):
        """ 清空显示 """
        self.content = self._new_content()
        self.setWidget(self.content)
        self.uuid_to_conversion_item = {}
    
    def _new_content(self) -> QWidget:
        content = QWidget()
        qss_formatter.add_widget(content, 'ScrollContent', QSSFiles.chat_window)
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 顶部对齐，不拉伸
        return content
    
    def __contains__(self, item: UUID|ConversionItem):
        if isinstance(item, UUID):
            return item in self.uuid_to_conversion_item.keys()
        elif isinstance(item, ConversionItem):
            return item in self.uuid_to_conversion_item.values()
        else:
            return False

    def start_edit(self, uuid: UUID):
        self.uuid_to_conversion_item[uuid].start_edit()
            