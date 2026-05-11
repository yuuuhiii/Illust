import math
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF
from items.math3d import rotate_3d, project_iso, compute_normal, generate_sphere, generate_cylinder_vertical

class IsoBlockItem(QGraphicsItemGroup):
    SNAP_ENABLED = True
    GRID_SIZE = 10

    def __init__(self, block_type="box", w=150, d=100, h=40, base_color=QColor(200, 200, 210), opacity=100):
        super().__init__()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.block_type = block_type
        self.w, self.d, self.h = w, d, h
        self.base_color = base_color
        self.opacity_val = opacity
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.rot_z = 0.0

        from PyQt6.QtWidgets import QGraphicsLineItem

        self.poly_items = []

        # Axes
        self.axis_x = QGraphicsLineItem()
        self.axis_y = QGraphicsLineItem()
        self.axis_z = QGraphicsLineItem()

        self.axis_x.setPen(QPen(Qt.GlobalColor.red, 2))
        self.axis_y.setPen(QPen(Qt.GlobalColor.green, 2))
        self.axis_z.setPen(QPen(Qt.GlobalColor.blue, 2))

        for ax in [self.axis_x, self.axis_y, self.axis_z]:
            ax.setParentItem(self)
            ax.hide()

        self.update_geometry()

    def _generate_mesh(self):
        faces = []

        # Origin maps to front top point as in original implementation.
        # Original:
        # X: right down (w)
        # Y: left down (d)
        # Z: up (h) but drawing went down for height.
        # Let's map X=w, Y=-d, Z=-h in standard space, then translate.

        # To match original IsoBlockItem exactly when rotations are 0:
        # Front top is 0,0.
        # X axis (width) goes in X direction.
        # Y axis (depth) goes in Y direction.
        # Z axis (height) goes down in 2D, which means -Z in our project_iso function?
        # Let's check project_iso: (x-y)*c, (x+y)*s - z.
        # Original v_right_top: (w*c, -w*s). Wait, project_iso for (w, 0, 0) gives (w*c, w*s).
        # Let's see: project_iso(x,y,z) = (x-y)*c, (x+y)*s - z.
        # Original v_right_top: x = w*c, y = w*s ? No, original says: x = w*c, y = -w*s.
        # Oh, if we use project_iso(w, 0, 0), it gives: x = w*c, y = w*s.
        # But wait, original says: v_right_top = (w*cos_a, -w*sin_a) -> this means it goes up-right.
        # Let's adjust coordinate generation for this block to match the original orientation.
        # If we just want a box:
        # We can construct the 8 vertices and then the 6 faces.

        x0, x1 = 0, self.w
        y0, y1 = 0, -self.d
        z0, z1 = 0, -self.h

        # Wait, if y=-self.d, then project_iso(0, -d, 0) = (+d*c, -d*s). Original v_left_top was (-d*c, -d*s).
        # Ah. project_iso(x,y,z) gives x_iso = (x-y)*c, y_iso = (x+y)*s - z.
        # To get x_iso = w*c, y_iso = w*s: let x=w, y=0, z=0. Then x_iso = w*c, y_iso = w*s. But original has -w*s.
        # Actually, in original code:
        # v_right_top = (w*cos_a, -w*sin_a) -> actually the screen Y axis goes down, so -w*sin_a means it goes UP on screen.
        # But project_iso(x, y, z) = ( (x-y)*c, (x+y)*s - z )
        # If we put (w, 0, 0) -> (w*c, w*s). This goes down-right.
        # The original code's "angle = math.radians(30)".
        # Let's check standard isometric projection in original IsoBlockItem:
        # v_front_top = (0, 0)
        # v_right_top = (w*c, -w*s)
        # v_left_top = (-d*c, -d*s)
        # v_back_top = ((w-d)*c, -(w+d)*s)
        # v_front_bottom = (0, h)

        # If we use project_iso(x,y,z):
        # We want to find mapping from (x,y,z) to original.
        # x_iso = (x-y)*c
        # y_iso = (x+y)*s - z
        # Let's map original vectors to (X,Y,Z) in our project_iso space:
        # v_right_top = (w*c, -w*s). If we set X=w, Y=0, Z=0 => x_iso=w*c, y_iso=w*s. We want -w*s. So let Z = 2*w*s? No, just flip Y-axis?
        # Actually, if we set X=0, Y=0, Z=0 => (0,0).
        # If we set X=w, Y=-w, Z=0 => x_iso=(w-(-w))*c = 2w*c... No.
        # Wait, what if we use X=w, Y=0, Z=2w*s ? No, X should just be width, Y should just be depth.
        # The original IsoBlockItem uses an isometric projection where both right and left axes go UP (-Y in screen).
        # This is a bit non-standard for games (usually they go down), but it's what it is.
        # Actually, in original project_iso:
        # def project_iso(x, y, z):
        #     return (x - y) * c, (x + y) * s - z
        # If we pass X=w, Y=0, Z=0 -> x_iso=w*c, y_iso=w*s.
        # But wait! IsoLineItem uses project_iso. Let's see how IsoLineItem looks.
        # IsoLineItem uses project_iso. Does it look consistent? Yes, probably.
        # So we should just use our standard X, Y, Z for the block, and let the user see it in the standard isometric space of the application!
        # If the standard space has X going down-right, Y going down-left, and Z going up, that's fine.
        # Wait, if X goes right-down and Y goes left-down:
        # X=(w,0,0) -> (w*c, w*s) -> right, down.
        # Y=(0,d,0) -> (-d*c, d*s) -> left, down.
        # Z=(0,0,h) -> (0, -h) -> up.
        # Let's construct a standard box based on this.

        # Vertices of the box
        # X: [0, w]
        # Y: [0, d]
        # Z: [0, -h]  (to make it grow downwards on screen, Z should be negative? In original, v_front_bottom is at +h on screen Y, which means Z goes DOWN. So Z=0 to -h)

        x0, x1 = 0, self.w
        y0, y1 = 0, self.d
        z0, z1 = 0, -self.h

        # 8 vertices
        v000 = (x0, y0, z0)
        v100 = (x1, y0, z0)
        v110 = (x1, y1, z0)
        v010 = (x0, y1, z0)
        v001 = (x0, y0, z1)
        v101 = (x1, y0, z1)
        v111 = (x1, y1, z1)
        v011 = (x0, y1, z1)

        faces = [
            [v000, v100, v110, v010], # Top (z=0)
            [v001, v011, v111, v101], # Bottom (z=-h)
            [v000, v010, v011, v001], # Left (x=0)
            [v100, v101, v111, v110], # Right (x=w)
            [v000, v001, v101, v100], # Front (y=0)
            [v010, v110, v111, v011], # Back (y=d)
        ]

        # We need to correctly align normals. The above vertices are ordered somewhat arbitrarily.
        # Let's order them counter-clockwise when looking from outside.
        faces = [
            [v000, v010, v110, v100], # Top (z=0, looking from top, normal -z. Wait, Z is down, so Top is Z=0. Normal: up)
            [v001, v101, v111, v011], # Bottom
            [v000, v001, v011, v010], # Front-Left (x=0)
            [v100, v110, v111, v101], # Back-Right (x=w)
            [v000, v100, v101, v001], # Front-Right (y=0)
            [v010, v011, v111, v110], # Back-Left (y=d)
        ]

        # Center of rotation should probably be the center of the block.
        cx = self.w / 2
        cy = self.d / 2
        cz = -self.h / 2

        # Shift to center, rotate, shift back
        rot_faces = []
        for face in faces:
            rot_face = []
            for px, py, pz in face:
                px -= cx
                py -= cy
                pz -= cz
                rx, ry, rz = rotate_3d(px, py, pz, self.rot_x, self.rot_y, self.rot_z)
                rx += cx
                ry += cy
                rz += cz
                rot_face.append((rx, ry, rz))
            rot_faces.append(rot_face)

        return rot_faces

    def update_geometry(self, block_type=None, w=None, d=None, h=None, base_color=None, opacity=None, rot_x=None, rot_y=None, rot_z=None):
        self.prepareGeometryChange()

        if block_type is not None: self.block_type = block_type
        if w is not None: self.w = w
        if d is not None: self.d = d
        if h is not None: self.h = h
        if base_color is not None: self.base_color = base_color
        if opacity is not None: self.opacity_val = max(10, min(100, opacity))
        if rot_x is not None: self.rot_x = rot_x
        if rot_y is not None: self.rot_y = rot_y
        if rot_z is not None: self.rot_z = rot_z

        self.setOpacity(self.opacity_val / 100.0)
        faces = self._generate_mesh()

        visible_faces = []
        for face in faces:
            nx, ny, nz = compute_normal(face)

            cx = sum(v[0] for v in face) / len(face)
            cy = sum(v[1] for v in face) / len(face)
            cz = sum(v[2] for v in face) / len(face)
            depth = cx + cy + cz

            # Simple lighting
            lx, ly, lz = 0.5, 1.0, 1.5
            ll = math.sqrt(lx*lx + ly*ly + lz*lz)
            dot = (nx*lx + ny*ly + nz*lz) / ll
            factor = 0.4 + 0.6 * (0.5 + 0.5 * dot)

            poly = QPolygonF()
            for rx, ry, rz in face:
                sx, sy = project_iso(rx, ry, rz)
                poly.append(QPointF(sx, sy))

            visible_faces.append({'poly': poly, 'depth': depth, 'factor': factor, 'normal': (nx, ny, nz)})

        visible_faces.sort(key=lambda f: f['depth'])

        # Clean up old polygons completely
        for p in self.poly_items:
            p.setParentItem(None)
            if self.scene():
                self.scene().removeItem(p)
        self.poly_items.clear()

        sel_pen = QPen(Qt.GlobalColor.blue, 2.0, Qt.PenStyle.DashLine)
        norm_pen = QPen(Qt.GlobalColor.black, 1.5)
        norm_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        for vf in visible_faces:
            # Backface culling: if normal points away from camera
            # Camera in iso is roughly (-1, -1, 1). Let's do simple dot product.
            # Actually depth sorting is enough, but wait, faces inside shouldn't be rendered.
            # Depth sorting draws back faces first, then front faces over them.
            item = QGraphicsPolygonItem()
            item.setPolygon(vf['poly'])
            r = min(255, max(0, int(self.base_color.red() * vf['factor'])))
            g = min(255, max(0, int(self.base_color.green() * vf['factor'])))
            b = min(255, max(0, int(self.base_color.blue() * vf['factor'])))
            item.setBrush(QBrush(QColor(r, g, b)))
            item.setPen(sel_pen if self.isSelected() else norm_pen)
            item.setParentItem(self)
            self.poly_items.append(item)

        self.axis_x.hide()
        self.axis_y.hide()
        self.axis_z.hide()

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            if self.SNAP_ENABLED:
                new_pos = value
                x = round(new_pos.x() / self.GRID_SIZE) * self.GRID_SIZE
                y = round(new_pos.y() / self.GRID_SIZE) * self.GRID_SIZE
                return QPointF(x, y)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_geometry()
        return super().itemChange(change, value)

    def clone(self):
        new_item = IsoBlockItem(block_type=self.block_type, w=self.w, d=self.d, h=self.h, base_color=self.base_color, opacity=self.opacity_val)
        new_item.rot_x = self.rot_x
        new_item.rot_y = self.rot_y
        new_item.rot_z = self.rot_z
        new_item.update_geometry()
        return new_item
