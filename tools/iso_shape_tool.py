from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import QPointF
from tools.base_tool import BaseTool
from items.iso_shape import IsoShapeItem

class DrawIsoShapeTool(BaseTool):
    def __init__(self, view, get_props_func):
        super().__init__(view)
        self.get_props_func = get_props_func
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def mousePressEvent(self, event):
        scene_pos = self.view.mapToScene(event.pos())

        if IsoShapeItem.SNAP_ENABLED:
            x = round(scene_pos.x() / IsoShapeItem.GRID_SIZE) * IsoShapeItem.GRID_SIZE
            y = round(scene_pos.y() / IsoShapeItem.GRID_SIZE) * IsoShapeItem.GRID_SIZE
            scene_pos = QPointF(x, y)

        shape_type, size, color, opacity, rot_x, rot_y, rot_z = self.get_props_func()
        shape = IsoShapeItem(shape_type=shape_type, size=size, base_color=color, opacity=opacity)
        shape.rot_x = rot_x
        shape.rot_y = rot_y
        shape.rot_z = rot_z
        shape.update_geometry()

        self.view.add_block(shape, scene_pos)

        self.scene.clearSelection()
        shape.setSelected(True)

        # Auto-switch to SelectTool
        from tools.select_tool import SelectTool
        self.view.tool_manager.set_tool(SelectTool(self.view))
        # Sync UI
        if hasattr(self.view.window(), 'sync_ui_to_selection'):
            self.view.window().sync_ui_to_selection()