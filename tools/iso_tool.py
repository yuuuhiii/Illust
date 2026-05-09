from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import QPointF
from tools.base_tool import BaseTool
from items.iso_block import IsoBlockItem

class DrawIsoBlockTool(BaseTool):
    def __init__(self, view, get_props_func):
        super().__init__(view)
        self.get_props_func = get_props_func
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def mousePressEvent(self, event):
        scene_pos = self.view.mapToScene(event.pos())
        
        if IsoBlockItem.SNAP_ENABLED:
            x = round(scene_pos.x() / IsoBlockItem.GRID_SIZE) * IsoBlockItem.GRID_SIZE
            y = round(scene_pos.y() / IsoBlockItem.GRID_SIZE) * IsoBlockItem.GRID_SIZE
            scene_pos = QPointF(x, y)

        w, d, h, color, opacity = self.get_props_func()
        block = IsoBlockItem(w=w, d=d, h=h, base_color=color, opacity=opacity)
        
        # キャンバス側の配列に登録させるために add_block を呼ぶ
        self.view.add_block(block, scene_pos)
        
        self.scene.clearSelection()
        block.setSelected(True)