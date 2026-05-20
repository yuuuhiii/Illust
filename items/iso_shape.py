import math
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF
from items.math3d import rotate_3d, project_iso, compute_normal

class IsoShapeItem(QGraphicsItemGroup):
    SNAP_ENABLED = True
    GRID_SIZE = 10

    def __init__(self, shape_type="square", size=100, base_color=QColor(200, 200, 210), opacity=100, custom_faces=None):
        super().__init__()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.shape_type = shape_type # "square" or "circle"
        self.size = size
        self.base_color = base_color
        self.opacity_val = opacity
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.rot_z = 0.0

        self.poly_item = QGraphicsPolygonItem()
        self.poly_item.setParentItem(self)

        self.custom_faces = custom_faces

        self.update_geometry()

    def _generate_mesh(self):
        if self.custom_faces is not None:
            return self.custom_faces

        faces = []
        r = self.size / 2.0

        # We define the shape on the XY plane, centered at origin
        # It's flat, so it's a single face
        if self.shape_type == "square":
            faces.append([(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)])
        elif self.shape_type == "circle":
            segments = 32
            face = []
            for i in range(segments):
                angle = i * 2 * math.pi / segments
                x = math.cos(angle) * r
                y = math.sin(angle) * r
                face.append((x, y, 0))
            faces.append(face)

        rot_faces = []
        for face in faces:
            rot_face = []
            for px, py, pz in face:
                rx, ry, rz = rotate_3d(px, py, pz, self.rot_x, self.rot_y, self.rot_z)
                rot_face.append((rx, ry, rz))
            rot_faces.append(rot_face)

        return rot_faces

    def update_geometry(self, shape_type=None, size=None, base_color=None, opacity=None, rot_x=None, rot_y=None, rot_z=None):
        self.prepareGeometryChange()

        if shape_type is not None: self.shape_type = shape_type
        if size is not None: self.size = max(1, size)
        if base_color is not None: self.base_color = base_color
        if opacity is not None: self.opacity_val = max(10, min(100, opacity))
        if rot_x is not None: self.rot_x = rot_x
        if rot_y is not None: self.rot_y = rot_y
        if rot_z is not None: self.rot_z = rot_z

        self.setOpacity(self.opacity_val / 100.0)
        faces = self._generate_mesh()

        if not faces:
            return

        face = faces[0] # Only one face for flat shape

        poly = QPolygonF()
        for rx, ry, rz in face:
            sx, sy = project_iso(rx, ry, rz)
            poly.append(QPointF(sx, sy))

        self.poly_item.setPolygon(poly)

        # Since it's flat, we don't need complex lighting, maybe just simple shading
        nx, ny, nz = compute_normal(face)
        # Fix backface normals
        if nx + ny + nz < 0:
            nx, ny, nz = -nx, -ny, -nz

        lx, ly, lz = 0.5, 1.0, 1.5
        ll = math.sqrt(lx*lx + ly*ly + lz*lz)
        dot = (nx*lx + ny*ly + nz*lz) / ll
        factor = 0.4 + 0.6 * (0.5 + 0.5 * dot)

        r = min(255, max(0, int(self.base_color.red() * factor)))
        g = min(255, max(0, int(self.base_color.green() * factor)))
        b = min(255, max(0, int(self.base_color.blue() * factor)))

        self.poly_item.setBrush(QBrush(QColor(r, g, b)))

        if self.isSelected():
            sel_pen = QPen(Qt.GlobalColor.blue, 2.0, Qt.PenStyle.DashLine)
            self.poly_item.setPen(sel_pen)
        else:
            norm_pen = QPen(Qt.GlobalColor.black, 1.5)
            norm_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            self.poly_item.setPen(norm_pen)

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
        new_item = IsoShapeItem(shape_type=self.shape_type, size=self.size, base_color=self.base_color, opacity=self.opacity_val)
        new_item.rot_x = self.rot_x
        new_item.rot_y = self.rot_y
        new_item.rot_z = self.rot_z
        new_item.update_geometry()
        return new_item


    def to_dict(self):
        d = {
            'type': 'IsoShapeItem',
            'pos': {'x': self.pos().x(), 'y': self.pos().y()},
            'zValue': self.zValue(),
            'shape_type': self.shape_type, 'size': self.size,
            'base_color': self.base_color.name(),
            'opacity': self.opacity_val,
            'rot_x': self.rot_x, 'rot_y': self.rot_y, 'rot_z': self.rot_z
        }
        if self.custom_faces is not None:
            d['custom_faces'] = self.custom_faces
        return d
