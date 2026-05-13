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
        
        # レイヤーの順序を管理する配列
        self.block_list = []

        self.tool_manager = ToolManager(self)
        self.tool_manager.set_tool(SelectTool(self))

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
        # Isometric Y sorting: higher Y means further down the screen -> front
        self.block_list.sort(key=lambda b: b.pos().y())
        for i, block in enumerate(self.block_list):
            block.setZValue(i)

    def mousePressEvent(self, event):
        self.tool_manager.mousePressEvent(event)
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        self.tool_manager.mouseMoveEvent(event)
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        self.tool_manager.mouseReleaseEvent(event)
        super().mouseReleaseEvent(event)
        if hasattr(self.window(), 'save_state'):
            self.window().save_state()