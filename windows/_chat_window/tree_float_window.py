from uuid import UUID
from IlinaEngine.type import IlinaMessage, IlinaMessageRoles
from PySide6.QtGui import QCursor, QPainter, QColor, QPainterPath
from PySide6.QtCore import Signal, Slot, Qt, QRectF
from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy, QVBoxLayout, QApplication, QPushButton

from QSS import qss_formatter, QSSFiles


class TreeFloatWindow(QWidget):
    """ 显示 Layout 节点信息 """
    
    move_to_node = Signal(UUID)
    delete_node = Signal(UUID)
    invoke_from_node = Signal(UUID)
    edit_node = Signal(UUID)

    def __init__(self):
        super().__init__()
        # 设置属性
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        # 透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 显示时不抢焦点
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # 显示角色的标题
        self.role_label = QLabel()
        qss_formatter.add_widget(self.role_label, 'LayoutNodeFloatWindowRole', QSSFiles.chat_window)

        # 显示内容
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        qss_formatter.add_widget(self.content_label, 'LayoutNodeFloatWindowContent', QSSFiles.chat_window)

        # 设置宽度
        self.content_label.setFixedWidth(qss_formatter.config.chat_window.float_window_fixed_width)
        self.content_label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Minimum
        )

        # 设置布局
        layout = QVBoxLayout(self)
        # 给自绘阴影预留空间
        layout.setContentsMargins(20, 20, 20, 20)
        # 添加元素
        layout.addWidget(self.role_label)
        layout.addWidget(self.content_label)
        layout.addWidget(self._setup_function_area())

        # 设置状态量
        self.Clicked: bool = False

        # 设置信号
        self.function_moveto.pressed.connect(self.on_moveto_pressed)
        self.function_delete.pressed.connect(self.on_delete_pressed)
        self.function_restart.pressed.connect(self.on_restart_pressed)
        self.function_edit.pressed.connect(self.on_edit_pressed)

        # 初始化更新
        self.update()

    def update(self) -> None:
        # 获取屏幕并判断是否超出屏幕，如果超出屏幕就移动
        screen = QApplication.screenAt(QCursor.pos()) 
        if screen:
            overflow = self.frameGeometry().bottom() - screen.availableGeometry().bottom()
            if overflow > 0:
                self.move(self.pos().x(), self.pos().y() - overflow)

        # 根据点击状态决定要不要显示按钮
        if self.Clicked:
            self.function_area.show()
        else:
            self.function_area.hide()
        
        # 根据节点类型判断按钮的状态（未实现的也设置成disabled了）
        self.function_edit.setEnabled(True)
        self.function_restart.setEnabled(True)
        self.function_moveto.setEnabled(True)
        self.function_delete.setEnabled(True)

        return super().update()

    def paintEvent(self, event):
        """ 绘制浮动窗口（自绘阴影 + 圆角背景）

        绘制分为两层（从外到内）：
          1. 阴影层：从 margin 最外层向内逐层绘制，alpha 递减
          2. 主背景层：圆角矩形，颜色 = 角色色，alpha 取决于是否被点击锁定
        """

        # ── 初始化 QPainter ────────────────────────────────────────
        # QPainter 是所有 Qt 自绘的入口，必须在 paintEvent 内构造
        painter = QPainter(self)
        # 开启抗锯齿，让圆角和阴影边缘平滑过渡
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ── 从全局 QSS 系统中读取配置 ──────────────────────────────
        # cfg: 非颜色配置（圆角半径、窗口尺寸等数字量）
        cfg = qss_formatter.config.chat_window
        # colors: 颜色配置（各角色的颜色值、透明度等）
        colors = qss_formatter.colors.chat_window
        # 圆角半径，例如 4px，控制浮窗四个角的弧度
        radius = cfg.float_window_radiu

        # ── 确定背景颜色与透明度 ────────────────────────────────────
        # 基础颜色取自 ROLE_COLOR_MAP，根据当前消息角色（user/assistant/tool/system）
        bg_color = QColor(colors.float_window_background_color)
        # bg_color = QColor(ROLE_COLOR_MAP[self.role])
        if not self.Clicked:
            # 未点击时：半透明，透明度从配置读取（如 128，即 50%）
            # 这样鼠标 hover 经过的浮窗不会完全遮挡下方内容
            bg_color.setAlpha(colors.float_window_background_alpha)
        else:
            # 点击锁定后：完全不透明（alpha=255）
            # 表示用户聚焦于该节点，浮窗应清晰可读
            bg_color.setAlpha(255)

        # ── 阴影外延宽度 ──────────────────────────────────────────
        # shadow_margin 决定阴影向外扩散多少像素
        # 这里的 6px 与 __init__ 中 layout.setContentsMargins(20,20,20,20)
        # 配合使用——margin 预留了阴影 + 额外的呼吸空间
        shadow_margin = 6

        # ── 确定内容区域矩形 ───────────────────────────────────────
        # self.rect() 是整个浮窗的完整区域（含 margin），
        # 用 adjusted(+m, +m, -m, -m) 从四边各向内收缩 shadow_margin，
        # 得到不含阴影的"内容矩形"作为主背景的范围
        rect = self.rect().adjusted(
            shadow_margin,    # 左边界右移
            shadow_margin,    # 上边界下移
            -shadow_margin,   # 右边界左移
            -shadow_margin    # 下边界上移
        )

        # ═══════════════════════════════════════════════════════════
        # 第一层：阴影（从外向内逐层绘制）
        # ═══════════════════════════════════════════════════════════
        # 原理：在内容矩形外围逐层画略大的圆角矩形，
        #       每层的 alpha 从高到低递减，模拟柔和扩散阴影。
        #
        # 例如 shadow_margin=6 时：
        #   i=0 → 紧贴内容矩形，alpha 最大（40）
        #   i=5 → 最外层，alpha 最小（≈7）
        #
        # 阴影颜色与角色色相同，保证浮窗和节点颜色一致。
        for i in range(shadow_margin):
            # ── 计算当前层的透明度 ─────────────────────────────────
            # alpha 从 40 线性递减到 ~7（最外层）
            #   i=0: alpha = 40 * (1 - 0/6) = 40
            #   i=5: alpha = 40 * (1 - 5/6) ≈ 7
            # 这种线性衰减让阴影从内到外自然淡出
            alpha = int(
                colors.float_window_shadow_start_alpha * (1 - i / shadow_margin)
            )

            # 阴影颜色 = 角色色 + 当前层透明度
            shadow_color = QColor(qss_formatter.get_role_color(self.role))
            shadow_color.setAlpha(alpha)

            # 阴影层不需要描边，只需要填充
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(shadow_color)

            # ── 绘制当前阴影层的圆角矩形 ────────────────────────────
            # rect.adjusted(-i, -i, i, i) 将矩形向四边各扩展 i 像素，
            # 形成比上一层大一圈的阴影环。
            # 圆角半径也要同步增大 radius + i，
            # 否则外层矩形圆角不够大会露出直角边缘。
            # 外层矩形
            outer_rect = rect.adjusted(
                -i,
                -i,
                i,
                i
            )

            # 外层路径
            outer_path = QPainterPath()
            outer_path.addRoundedRect(
                QRectF(outer_rect),
                radius + i,
                radius + i
            )

            # 内层路径
            inner_path = QPainterPath()
            inner_path.addRoundedRect(
                QRectF(rect),
                radius,
                radius
            )

            # 环 = 外层 - 内层
            ring_path = outer_path.subtracted(inner_path)

            # 绘制环
            painter.fillPath(
                ring_path,
                shadow_color
            )
        # ═══════════════════════════════════════════════════════════
        # 第二层：主背景（圆角矩形，覆盖在阴影之上）
        # ═══════════════════════════════════════════════════════════
        # 在阴影全部画完之后，再画紧贴内容矩形的背景。
        # 这样主背景会自然地"盖在"阴影上面，
        # 从视觉上看就是"圆角矩形 + 向外扩散的柔和阴影"。
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)

        painter.drawRoundedRect(
            rect,          # 内容矩形，和阴影最内层（i=0）位置完全一致
            radius,        # 圆角半径，使用配置值
            radius
        )

    def set_node(self, node_uuid: UUID, node_message: IlinaMessage):
        """ 设置节点 """
        self.node_uuid = node_uuid  # 这个后面用在按钮出发事件时传递节点 UUID 确定点击的是哪个节点
        self.role_label.setText(node_message.role.title())
        self.role: IlinaMessageRoles = node_message.role
        self.content_label.setText(
            node_message.content[:50].replace('\n', '')  
        + ('...' if len(node_message.content) > 50 else '')) 

        # 移动鼠标和重绘
        self.move(QCursor.pos())
        self.update()
    
    def _setup_function_area(self) -> QWidget:

        # 编辑按钮
        self.function_edit = QPushButton()
        self.function_edit.setText('编辑')
        qss_formatter.add_widget(self.function_edit, 'FloatWindowFunctionButton', QSSFiles.chat_window)

        # 重新生成按钮
        self.function_restart = QPushButton()
        self.function_restart.setText('重新生成')
        qss_formatter.add_widget(self.function_restart, 'FloatWindowFunctionButton', QSSFiles.chat_window)

        # 切换到按钮
        self.function_moveto = QPushButton()
        self.function_moveto.setText('切换到此')
        qss_formatter.add_widget(self.function_moveto, 'FloatWindowFunctionButton', QSSFiles.chat_window)

        # 删除到按钮
        self.function_delete = QPushButton()
        self.function_delete.setText('删除')
        qss_formatter.add_widget(self.function_delete, 'FloatWindowFunctionButton', QSSFiles.chat_window)

        # 功能区本身
        self.function_area = QWidget()
        qss_formatter.add_widget(self.function_area, 'FloatWindowFunctionArea', QSSFiles.chat_window)

        layout = QVBoxLayout(self.function_area)
        layout.setSpacing(0)
        layout.addWidget(self.function_moveto)
        layout.addWidget(self.function_edit)
        layout.addWidget(self.function_restart)
        layout.addWidget(self.function_delete)

        return self.function_area

    @Slot()
    def on_moveto_pressed(self):
        self.move_to_node.emit(self.node_uuid)
    
    @Slot()
    def on_delete_pressed(self):
        self.delete_node.emit(self.node_uuid)
    
    @Slot()
    def on_restart_pressed(self):
        self.invoke_from_node.emit(self.node_uuid)
    
    @Slot()
    def on_edit_pressed(self):
        self.edit_node.emit(self.node_uuid)