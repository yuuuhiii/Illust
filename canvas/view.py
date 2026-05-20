from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QPainter
from tools.manager import ToolManager
from tools.select_tool import SelectTool

class CanvasView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 1000, 800)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # ズーム時の基準点をマウスカーソルの位置に設定
        from PyQt6.QtWidgets import QGraphicsView
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # レイヤーの順序を管理する配列
        self.block_list = []

        self.tool_manager = ToolManager(self)
        self.tool_manager.set_tool(SelectTool(self))

        # パン操作用の状態変数
        self._is_panning = False
        self._pan_start_pos = None

    def add_block(self, block, pos):
        self.scene.addItem(block)
        block.setPos(pos)
        self.block_list.append(block)
        self.update_z_values()
        if hasattr(self.window(), 'save_state'):
            self.window().save_state()

    def remove_block(self, block):
        """ブロックを削除し, 配列からも取り除く"""
        if block in self.block_list:
            self.block_list.remove(block)
        self.scene.removeItem(block)
        self.update_z_values()

    def move_front(self, block):
        """配列のインデックスを1つ後ろ(前面)と入れ替える"""
        if block in self.block_list:
            idx = self.block_list.index(block)
            if idx < len(self.block_list) - 1:
                self.block_list[idx], self.block_list[idx+1] = self.block_list[idx+1], self.block_list[idx]
                self.update_z_values()

    def move_back(self, block):
        """配列のインデックスを1つ前(背面)と入れ替える"""
        if block in self.block_list:
            idx = self.block_list.index(block)
            if idx > 0:
                self.block_list[idx], self.block_list[idx-1] = self.block_list[idx-1], self.block_list[idx]
                self.update_z_values()

    def update_z_values(self):
        """現在の配列の並び順通りにZインデックスを振り直す"""
        for i, block in enumerate(self.block_list):
            block.setZValue(i)

    def mousePressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
            
        self.tool_manager.mousePressEvent(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning and self._pan_start_pos is not None:
            delta = event.pos() - self._pan_start_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._pan_start_pos = event.pos()
            event.accept()
            return
            
        self.tool_manager.mouseMoveEvent(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.button() == Qt.MouseButton.MiddleButton and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
            
        self.tool_manager.mouseReleaseEvent(event)
        super().mouseReleaseEvent(event)
        
        # 中ボタンでのリリースでは save_state は呼ばない
        if event.button() != Qt.MouseButton.MiddleButton:
            if hasattr(self.window(), 'save_state'):
                self.window().save_state()

    def wheelEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # マウスホイールによるズーム
            if event.angleDelta().y() > 0:
                self.scale(1.15, 1.15)
            else:
                self.scale(1 / 1.15, 1 / 1.15)
        else:
            super().wheelEvent(event)