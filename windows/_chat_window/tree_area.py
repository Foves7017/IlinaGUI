import logging
from uuid import UUID
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt, QRectF, Signal, Slot
from PySide6.QtWidgets import QWidget, QGraphicsScene, QGraphicsView, QVBoxLayout, QGraphicsLineItem
from IlinaEngine.type import Node

from .tree_node import TreeNode

from QSS import qss_formatter, QSSFiles

class TreeArea(QGraphicsView):
    tree_node_enter = Signal(UUID)
    tree_node_left = Signal(UUID)
    tree_node_click = Signal(UUID)

    def __init__(self):
        self.log = logging.getLogger('树视图')

        # 场景和视角
        self.tree_scene = QGraphicsScene()
        super().__init__(self.tree_scene)
        qss_formatter.add_widget(self, 'TreeView', QSSFiles.chat_window)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def draw(self, root_node: Node, leaves: list[Node]):
        self.log.info(f'开始重绘树')
        self.tree_scene.clear()
        # 建立树节点到绘图节点的映射表，并设置层坐标
        table: dict[Node, TreeNode] = {}
        def update_table(node: Node, deepth: int):
            if node not in table:
                table[node] = TreeNode(node.message.role, node.uuid, deepth, 
                                         qss_formatter.config.chat_window.tree_node_radiu,
                                         qss_formatter.config.chat_window.tree_node_space,
                                         )
                table[node].hover_entered.connect(lambda uuid: self.tree_node_enter.emit(uuid))
                table[node].hover_left.connect(lambda uuid: self.tree_node_left.emit(uuid))
                for child in node.children:
                    update_table(child, deepth+1)
        update_table(root_node, 0)

        # 获取所有叶子节点，并为其指定纵坐标
        for i, leaf in enumerate(leaves):
            table[leaf].columnpos = i 
        
        # 为所有未分配纵坐标的叶子节点指定纵坐标
        def get_column(node: Node) -> int:
            column = table[node].columnpos
            if table[node].columnpos is None:  # 没有指定纵坐标
                # 获取所有子节点的纵坐标
                for child in node.children:
                    get_column(child)
                child = node._get_pointed_child()
                if child is not None:  # 子节点没有指定纵坐标
                    column = get_column(child)  # 向下寻找
                    table[node].columnpos = column
                else:
                    raise RuntimeError(f'节点 {node.uuid} 没有 column，且没有可追踪的 pointed child')
            assert column is not None
            return column
        root_column = get_column(root_node)

        # 把所有节点的纵坐标都减去根节点的纵坐标，这样可以居中，并结合设置的行列确定最终的坐标
        max_layer = -1
        for node in table:
            max_layer = max(max_layer, table[node].layer)
            table[node].columnpos -= root_column # pyright: ignore[reportOperatorIssue]
        # 同时也调节一下layer坐标，同样是为了居中
        max_layer = max_layer / 2 + 0.5
        for node in table:
            table[node].layer -= max_layer
            table[node].set_position()
            self.tree_scene.addItem(table[node])
        
        # 递归画线
        def line_to_children(node: Node):
            for child in node.children:
                line = QGraphicsLineItem(table[node].x(), table[node].y(), table[child].x(), table[child].y())
                line.setPen(QPen(
                    QColor(qss_formatter.colors.chat_window.role_line_color),
                    qss_formatter.config.chat_window.tree_node_line_width)
                )
                line.setZValue(0)
                self.tree_scene.addItem(line)
                line_to_children(child)
        line_to_children(root_node)

        # 固定场景矩形，确保原点 (0,0) 处于视图中心
        rect = self.tree_scene.itemsBoundingRect()
        half_w = max(abs(rect.left()), abs(rect.right())) + 50
        half_h = max(abs(rect.top()), abs(rect.bottom())) + 50
        self.tree_scene.setSceneRect(
            QRectF(-half_w, -half_h, half_w * 2, half_h * 2)
        )
        self.centerOn(0, 0)

        # 绑定信号
        self.tree_scene.selectionChanged.connect(self.on_selection_changed)
        self.log.info(f'重绘树完成')
    
    def on_selection_changed(self):
        try:
            layout_node: TreeNode = self.tree_scene.selectedItems()[0]  # pyright: ignore[reportAssignmentType]
            self.tree_node_click.emit(layout_node.node_uuid)
        except IndexError:
            pass