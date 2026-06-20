from uuid import UUID
from PySide6.QtCore import Signal, Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (QGraphicsObject, QGraphicsItem, QGraphicsSceneHoverEvent, 
                               QStyleOptionGraphicsItem, QStyle)

from IlinaEngine.type import IlinaMessageRoles
from QSS import qss_formatter, QSSFiles

class TreeNode(QGraphicsObject):
    hover_entered = Signal(UUID)
    hover_left = Signal(UUID)
    
    def __init__(self, node_role: IlinaMessageRoles, node_uuid, layer: int, radiu: int, space: int):
        super().__init__()
        self.node_role: IlinaMessageRoles = node_role
        self.node_uuid = node_uuid  # 用于发送事件
        self.layer: int|float = layer
        self.columnpos: int|None = None
        self.radiu = radiu
        self.space = space

        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    
        # 设置 hover 信号
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.hover_entered.emit(self.node_uuid)
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.hover_left.emit(self.node_uuid)
        return super().hoverLeaveEvent(event)

    def set_position(self):
        assert self.columnpos is not None
        self.setPos(
            self.columnpos*(2*self.radiu+self.space),
            self.layer*(2*self.radiu+self.space),
        )

    def boundingRect(self) -> QRectF:
        return QRectF(
            -self.radiu-(self.space//2),
            -self.radiu-(self.space//2),
            2*self.radiu+self.space,
            2*self.radiu+self.space,
        )
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None) -> None:
        color = QColor(qss_formatter.get_role_color(self.node_role))
        painter.setBrush(QColor(color))
        if self.columnpos == 0:
            painter.setPen(QPen(QColor(qss_formatter.colors.chat_window.role_line_color), 
                                qss_formatter.config.chat_window.tree_node_line_width))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(-self.radiu, -self.radiu, self.radiu*2, self.radiu*2)

        if option.state & QStyle.StateFlag.State_MouseOver:
            painter.setBrush(QBrush())
            painter.setPen(QPen(QColor(qss_formatter.colors.chat_window.role_line_color), 1))
            circ_r = 5
            painter.drawEllipse(-self.radiu - circ_r, -self.radiu - circ_r, self.radiu*2 + circ_r*2, self.radiu*2 + circ_r*2)
