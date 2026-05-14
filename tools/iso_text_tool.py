from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import QPointF
from tools.base_tool import BaseTool
from items.iso_text import IsoTextItem

class DrawIsoTextTool(BaseTool):
    def __init__(self, view, get_props_func):
        super().__init__(view)
        self.get_props_func = get_props_func
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def mousePressEvent(self, event):
        scene_pos = self.view.mapToScene(event.pos())

        if IsoTextItem.SNAP_ENABLED:
            x = round(scene_pos.x() / IsoTextItem.GRID_SIZE) * IsoTextItem.GRID_SIZE
            y = round(scene_pos.y() / IsoTextItem.GRID_SIZE) * IsoTextItem.GRID_SIZE
            scene_pos = QPointF(x, y)

        text, font_size, plane, color, opacity = self.get_props_func()
        text_item = IsoTextItem(text=text, font_size=font_size, plane=plane, base_color=color, opacity=opacity)

        self.view.add_block(text_item, scene_pos)

        self.scene.clearSelection()
        text_item.setSelected(True)

        # Auto-switch to SelectTool
        from tools.select_tool import SelectTool
        self.view.tool_manager.set_tool(SelectTool(self.view))
        # Sync UI
        if hasattr(self.view.window(), 'sync_ui_to_selection'):
            self.view.window().sync_ui_to_selection()