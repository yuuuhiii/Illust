import math
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPointF
from tools.base_tool import BaseTool
from items.iso_polyline import IsoPolylineItem

class DrawIsoPolylineTool(BaseTool):
    def __init__(self, view, get_props_func):
        super().__init__(view)
        self.get_props_func = get_props_func
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.current_item = None
        self.points_3d = []

    def _screen_to_iso_grid(self, screen_pos):
        """
        Inverse projection from isometric screen coordinates (sx, sy) to 3D grid coordinates (X, Y) on the floor plane (Z=0).
        sx = (X - Y) * cos(30)
        sy = (X + Y) * sin(30)
        """
        angle = math.radians(30)
        c, s = math.cos(angle), math.sin(angle)

        # sx / c = X - Y
        # sy / s = X + Y
        A = screen_pos.x() / c
        B = screen_pos.y() / s

        # A + B = 2X => X = (A + B) / 2
        X = (A + B) / 2.0
        # B - A = 2Y => Y = (B - A) / 2
        Y = (B - A) / 2.0

        if IsoPolylineItem.SNAP_ENABLED:
            X = round(X / IsoPolylineItem.GRID_SIZE) * IsoPolylineItem.GRID_SIZE
            Y = round(Y / IsoPolylineItem.GRID_SIZE) * IsoPolylineItem.GRID_SIZE

        return QPointF(X, Y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.view.mapToScene(event.pos())
            grid_pos = self._screen_to_iso_grid(scene_pos)

            if self.current_item is None:
                thickness, color, opacity = self.get_props_func()
                self.points_3d = [grid_pos]
                self.current_item = IsoPolylineItem(points=list(self.points_3d), thickness=thickness, base_color=color, opacity=opacity)
                self.view.add_block(self.current_item, QPointF(0, 0)) # Polyline handles its own absolute coords internally
            else:
                self.points_3d.append(grid_pos)
                self.current_item.update_geometry(points=list(self.points_3d))

        elif event.button() == Qt.MouseButton.RightButton:
            self._finish_drawing()

    def mouseMoveEvent(self, event):
        if self.current_item:
            scene_pos = self.view.mapToScene(event.pos())
            grid_pos = self._screen_to_iso_grid(scene_pos)

            temp_points = list(self.points_3d)
            temp_points.append(grid_pos)
            self.current_item.update_geometry(points=temp_points)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._finish_drawing()

    def _finish_drawing(self):
        if self.current_item:
            if len(self.points_3d) < 2:
                self.view.remove_block(self.current_item)
            else:
                self.current_item.update_geometry(points=list(self.points_3d))
                self.scene.clearSelection()
                self.current_item.setSelected(True)
            self.current_item = None
            self.points_3d = []

            from tools.select_tool import SelectTool
            self.view.tool_manager.set_tool(SelectTool(self.view))
            if hasattr(self.view.window(), 'sync_ui_to_selection'):
                self.view.window().sync_ui_to_selection()
