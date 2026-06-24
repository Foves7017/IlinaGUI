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
        """绘制树节点图形。

        分为两层绘制：
        1. **基础圆点**：带填充色的实心圆，颜色由当前节点的角色决定。
           - columnpos == 0（首列/树根列）：额外绘制边框，使用 tree_line_color + tree_node_line_width
           - 其他列：无边框（NoPen），形成"从根节点向外逐渐淡化"的视觉效果
        2. **Hover 光环**：当鼠标悬停在节点上时，在基础圆点外围绘制一圈
           空心圆环（半径扩大 5px），表示当前节点可交互。
        """
        # ===== 第一层：基础圆点 =====
        # 根据节点的角色（user/assistant/system 等）从 QSS 配色方案中获取对应颜色
        # 改成跟列使用亮色
        painter.setPen(Qt.PenStyle.NoPen)
        if self.columnpos == 0:
            color = QColor(qss_formatter.get_role_color(self.node_role))
        else:
            color = QColor(qss_formatter.get_role_color(self.node_role, True))
        painter.setBrush(QColor(color))

        # if self.columnpos == 0:
        #     # 首列节点（树结构的"根列"）使用带颜色的边框，
        #     # 边框颜色和宽度来自 QSS 配置，保持与聊天窗口角色线条一致的视觉风格
        #     painter.setPen(QPen(QColor(qss_formatter.colors.chat_window.tree_line_color),
        #                         qss_formatter.config.chat_window.tree_node_line_width))
        # else:
        #     # 非首列节点不绘制边框，让树结构视觉上从根向外逐层弱化
        #     painter.setPen(Qt.PenStyle.NoPen)
        


        # 绘制实心圆：圆心在 (0, 0)，半径为 self.radiu
        # drawEllipse 参数为外接矩形：(x, y, width, height)
        painter.drawEllipse(-self.radiu, -self.radiu, self.radiu * 2, self.radiu * 2)

        # ===== 第二层：Hover 光环 =====
        # 当鼠标悬停在节点上时，绘制外围的空心圆环作为交互提示
        if option.state & QStyle.StateFlag.State_MouseOver:
            painter.setBrush(QBrush())  # 空心：不填充
            painter.setPen(QPen(QColor(qss_formatter.colors.chat_window.tree_line_color), 1))
            circ_r = 5  # 光环与基础圆之间的间距（像素）
            painter.drawEllipse(
                -self.radiu - circ_r, -self.radiu - circ_r,
                self.radiu * 2 + circ_r * 2, self.radiu * 2 + circ_r * 2
            )
