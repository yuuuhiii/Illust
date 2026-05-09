import math
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QColor
from tools.base_tool import BaseTool
from items.iso_line import IsoLineItem

class DrawIsoLineTool(BaseTool):
    def __init__(self, view, get_props_func):
        super().__init__(view)
        self.get_props_func = get_props_func
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.start_pos = None
        self.preview_item = None

    def mousePressEvent(self, event):
        scene_pos = self.view.mapToScene(event.pos())

        if IsoLineItem.SNAP_ENABLED:
            x = round(scene_pos.x() / IsoLineItem.GRID_SIZE) * IsoLineItem.GRID_SIZE
            y = round(scene_pos.y() / IsoLineItem.GRID_SIZE) * IsoLineItem.GRID_SIZE
            scene_pos = QPointF(x, y)

        if self.start_pos is None:
            # First click
            self.start_pos = scene_pos
            thickness, arrow_type, color, opacity, _, _, _ = self.get_props_func()
            self.preview_item = IsoLineItem(length=1, thickness=thickness, arrow_type=arrow_type, base_color=color, opacity=opacity)
            self.view.scene.addItem(self.preview_item)
            self.preview_item.setPos(scene_pos)
        else:
            # Second click
            final_pos = self._get_snapped_pos(self.start_pos, scene_pos)
            dx = final_pos.x() - self.start_pos.x()
            dy = final_pos.y() - self.start_pos.y()

            # Iso axes vectors (2D representation)
            # x_axis: (cos 30, sin 30)
            # y_axis: (-cos 30, sin 30)
            # z_axis: (0, -1)

            angle = math.radians(30)
            c, s = math.cos(angle), math.sin(angle)

            # Determine 3D length and rotation based on the snapped vector
            length_2d = math.hypot(dx, dy)
            length_3d = 0
            rot_z = 0

            if length_2d > 0.1:
                dir_x = dx / length_2d
                dir_y = dy / length_2d

                dot_x = dir_x * c + dir_y * s
                dot_y = dir_x * (-c) + dir_y * s
                dot_z = dir_x * 0 + dir_y * (-1)

                max_dot = max(abs(dot_x), abs(dot_y), abs(dot_z))

                if max_dot == abs(dot_x): # aligned to X axis
                    length_3d = length_2d / c
                    rot_z = 0 if dot_x > 0 else 180
                elif max_dot == abs(dot_y): # aligned to Y axis
                    length_3d = length_2d / c
                    rot_z = -90 if dot_y > 0 else 90
                else: # aligned to Z axis
                    length_3d = length_2d
                    # Actually drawing along Z axis requires rotating the object around Y axis
                    # Our default cylinder is along X axis.
                    # Rotating 90 deg around Y points it to Z
                    rot_y = -90 if dot_z > 0 else 90

            thickness, arrow_type, color, opacity, _, _, _ = self.get_props_func()

            if self.preview_item:
                self.view.scene.removeItem(self.preview_item)
                self.preview_item = None

            center_x = (self.start_pos.x() + final_pos.x()) / 2
            center_y = (self.start_pos.y() + final_pos.y()) / 2

            if length_3d > 0.1:
                block = IsoLineItem(length=length_3d, thickness=thickness, arrow_type=arrow_type, base_color=color, opacity=opacity)

                if max_dot == abs(dot_z):
                    block.update_geometry(rot_y=-90 if dot_z > 0 else 90)
                else:
                    block.update_geometry(rot_z=rot_z)

                self.view.add_block(block, QPointF(center_x, center_y))
                self.scene.clearSelection()
                block.setSelected(True)

            self.start_pos = None

    def mouseMoveEvent(self, event):
        if self.start_pos is None or self.preview_item is None:
            return

        scene_pos = self.view.mapToScene(event.pos())
        final_pos = self._get_snapped_pos(self.start_pos, scene_pos)

        dx = final_pos.x() - self.start_pos.x()
        dy = final_pos.y() - self.start_pos.y()

        angle = math.radians(30)
        c, s = math.cos(angle), math.sin(angle)

        length_2d = math.hypot(dx, dy)
        if length_2d < 0.1:
            self.preview_item.update_geometry(length=1)
            return

        dir_x = dx / length_2d
        dir_y = dy / length_2d

        dot_x = dir_x * c + dir_y * s
        dot_y = dir_x * (-c) + dir_y * s
        dot_z = dir_x * 0 + dir_y * (-1)

        max_dot = max(abs(dot_x), abs(dot_y), abs(dot_z))

        length_3d = 0
        rot_y = 0
        rot_z = 0

        if max_dot == abs(dot_x):
            length_3d = length_2d / c
            rot_z = 0 if dot_x > 0 else 180
        elif max_dot == abs(dot_y):
            length_3d = length_2d / c
            rot_z = -90 if dot_y > 0 else 90
        else:
            length_3d = length_2d
            rot_y = -90 if dot_z > 0 else 90

        center_x = (self.start_pos.x() + final_pos.x()) / 2
        center_y = (self.start_pos.y() + final_pos.y()) / 2

        self.preview_item.setPos(center_x, center_y)
        self.preview_item.update_geometry(length=length_3d, rot_y=rot_y, rot_z=rot_z)

    def _get_snapped_pos(self, start, current):
        dx = current.x() - start.x()
        dy = current.y() - start.y()

        length = math.hypot(dx, dy)
        if length < 0.1: return current

        dir_x = dx / length
        dir_y = dy / length

        angle = math.radians(30)
        c, s = math.cos(angle), math.sin(angle)

        # Directions: X, -X, Y, -Y, Z, -Z
        dirs = [
            (c, s), (-c, -s),
            (-c, s), (c, -s),
            (0, -1), (0, 1)
        ]

        best_dir = dirs[0]
        max_dot = -1

        for d in dirs:
            dot = dir_x * d[0] + dir_y * d[1]
            if dot > max_dot:
                max_dot = dot
                best_dir = d

        # Project vector onto best_dir
        proj_length = max_dot * length

        snap_x = start.x() + best_dir[0] * proj_length
        snap_y = start.y() + best_dir[1] * proj_length

        if IsoLineItem.SNAP_ENABLED:
            snap_x = round(snap_x / IsoLineItem.GRID_SIZE) * IsoLineItem.GRID_SIZE
            snap_y = round(snap_y / IsoLineItem.GRID_SIZE) * IsoLineItem.GRID_SIZE

        return QPointF(snap_x, snap_y)
