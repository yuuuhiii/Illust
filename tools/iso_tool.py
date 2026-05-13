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
            sx = scene_pos.x()
            sy = scene_pos.y()
            import math
            c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
            iso_x = (sx / c + sy / s) / 2
            iso_y = (sy / s - sx / c) / 2
            iso_x = round(iso_x / IsoBlockItem.GRID_SIZE) * IsoBlockItem.GRID_SIZE
            iso_y = round(iso_y / IsoBlockItem.GRID_SIZE) * IsoBlockItem.GRID_SIZE
            snap_sx = (iso_x - iso_y) * c
            snap_sy = (iso_x + iso_y) * s
            scene_pos = QPointF(snap_sx, snap_sy)

        w, d, h, color, opacity = self.get_props_func()
        block = IsoBlockItem(w=w, d=d, h=h, base_color=color, opacity=opacity)
        
        # キャンバス側の配列に登録させるために add_block を呼ぶ
        self.view.add_block(block, scene_pos)
        
        self.scene.clearSelection()
        block.setSelected(True)