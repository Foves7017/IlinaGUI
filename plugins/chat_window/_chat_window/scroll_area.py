import logging
from uuid import UUID
from FovesConfig import ConfigLoader
from PySide6.QtGui import QPaintEvent, QWheelEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy
from PySide6.QtCore import Qt, Signal, QTimer
from IlinaEngine import IlinaMessage

from utils import app_dir
from .conversion_item import ConversionItem

from layout.formatter import Formatter
from ..consts import ChatWindowConfig, QSS_FILEPATH, CONFIG_PATH

class ScrollArea(QScrollArea):
    start_edit_node = Signal(UUID)
    edit_finished = Signal(UUID, IlinaMessage, bool)  # 编辑完成的信号
    invoke_from_node = Signal(UUID)

    def __init__(self, formatter: Formatter):
        super().__init__()
        self.formatter = formatter
        
        self.log = logging.getLogger('滚动区域')
        self.setObjectName('ScrollArea')
        self.setWidgetResizable(True)  # 内容 widget 随滚动区域自适应宽度
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 是否自动滚动
        self.auto: bool = True
        # 自动滚动的目标
        self.target_scroll_uuid: UUID|None = None

        # 滚动区域内部的内容容器
        self.content = self._new_content()
        self.setWidget(self.content)

        # UUID 到 Item 的记录表
        self.uuid_to_conversion_item: dict[UUID, ConversionItem] = {}
        self.last_item: UUID   # 最下面的节点
    
    def wheelEvent(self, arg__1: QWheelEvent) -> None:
        self.auto = False
        return super().wheelEvent(arg__1)

    def paintEvent(self, arg__1: QPaintEvent) -> None:
        self.content_layout.setContentsMargins(0, 0, 0, self.height()*2)  # 添加空白

        if self.auto:
            speed = ConfigLoader(CONFIG_PATH, ChatWindowConfig).readonly().scroll_speed
            value = self.verticalScrollBar().value()         

            if self.target_scroll_uuid:
                # 滚动到目标
                itempos = self.uuid_to_conversion_item[self.target_scroll_uuid].geometry().top()

                if itempos < value - speed:
                    self.verticalScrollBar().setValue(value - speed)
                elif itempos > value + speed:
                    self.verticalScrollBar().setValue(value + speed)
                elif value - speed < itempos < value + speed:
                    self.verticalScrollBar().setValue(itempos)
                else:
                    self.auto = False
            else:
                self.content_layout.setContentsMargins(0, 0, 0, 0)  # 添加空白
                itempos = self.uuid_to_conversion_item[self.last_item].geometry().bottom()
                if value + self.height() < itempos:
                    if value + self.height() - itempos < speed:
                        self.verticalScrollBar().setValue(itempos)
                    else:
                        self.verticalScrollBar().setValue(value + speed)

        super().paintEvent(arg__1)
        self.update()


    def update_item(self, uuid: UUID, new_message: IlinaMessage):
        """ 更新节点 """
        item = self.uuid_to_conversion_item[uuid]
        item.update_message(new_message)

    def add_messages(self, uuids: list[UUID], messages: list[IlinaMessage]):
        """ 向区域内添加节点 """
        for uuid, message in zip(uuids, messages):
            self.log.debug(f'添加节点：{uuid}')
            new_item = ConversionItem(uuid, message, self.formatter)
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
        content.setObjectName('ScrollContent')
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(0)
        self.content_layout.setContentsMargins(0, 0, 0, self.height()*2)
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
            