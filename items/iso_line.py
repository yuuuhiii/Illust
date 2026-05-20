import math
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF
from items.math3d import rotate_3d, project_iso, compute_normal

def generate_cylinder(radius, length, segments=36, offset_x=0):
    faces = []
    # Subdivide long cylinders to fix depth sorting
    length_segments = 1
    seg_len = length / length_segments

    for ls in range(length_segments):
        x1 = offset_x + ls * seg_len
        x2 = offset_x + (ls + 1) * seg_len
        for i in range(segments):
            a1 = i * 2 * math.pi / segments
            a2 = (i + 1) * 2 * math.pi / segments
            y1, z1 = math.cos(a1) * radius, math.sin(a1) * radius
            y2, z2 = math.cos(a2) * radius, math.sin(a2) * radius
            faces.append([(x1, y1, z1), (x1, y2, z2), (x2, y2, z2), (x2, y1, z1)])

    # Caps
    faces.append([(offset_x, math.cos(j * 2 * math.pi / segments) * radius, math.sin(j * 2 * math.pi / segments) * radius) for j in range(segments)][::-1])
    faces.append([(offset_x + length, math.cos(j * 2 * math.pi / segments) * radius, math.sin(j * 2 * math.pi / segments) * radius) for j in range(segments)])
    return faces

def generate_cone(radius, length, segments=36, offset_x=0):
    faces = []
    x1, x2 = offset_x, offset_x + length
    for i in range(segments):
        a1 = i * 2 * math.pi / segments
        a2 = (i + 1) * 2 * math.pi / segments
        y1, z1 = math.cos(a1) * radius, math.sin(a1) * radius
        y2, z2 = math.cos(a2) * radius, math.sin(a2) * radius
        faces.append([(x1, y1, z1), (x1, y2, z2), (x2, 0, 0)])
    faces.append([(x1, math.cos(j * 2 * math.pi / segments) * radius, math.sin(j * 2 * math.pi / segments) * radius) for j in range(segments)][::-1])
    return faces

def generate_box(length, width, height, offset_x=0):
    faces = []
    length_segments = 1
    seg_len = length / length_segments
    w, h = width / 2, height / 2

    for ls in range(length_segments):
        x1 = offset_x + ls * seg_len
        x2 = offset_x + (ls + 1) * seg_len
        faces.extend([
            [(x1, w, -h), (x2, w, -h), (x2, -w, -h), (x1, -w, -h)],
            [(x1, -w, h), (x2, -w, h), (x2, w, h), (x1, w, h)],
            [(x1, -w, -h), (x2, -w, -h), (x2, -w, h), (x1, -w, h)],
            [(x1, w, h), (x2, w, h), (x2, w, -h), (x1, w, -h)],
        ])

    faces.extend([
        [(offset_x, -w, -h), (offset_x, -w, h), (offset_x, w, h), (offset_x, w, -h)],
        [(offset_x + length, w, -h), (offset_x + length, w, h), (offset_x + length, -w, h), (offset_x + length, -w, -h)]
    ])
    return faces
def generate_flat_arrow(width, length, height, offset_x=0):
    x1, x2 = offset_x, offset_x + length
    w, h = width / 2, height / 2
    return [
        [(x1, w, -h), (x2, 0, -h), (x1, -w, -h)],
        [(x1, -w, h), (x2, 0, h), (x1, w, h)],
        [(x1, -w, -h), (x2, 0, -h), (x2, 0, h), (x1, -w, h)],
        [(x1, w, h), (x2, 0, h), (x2, 0, -h), (x1, w, -h)],
        [(x1, -w, -h), (x1, -w, h), (x1, w, h), (x1, w, -h)]
    ]

class IsoLineItem(QGraphicsItemGroup):
    SNAP_ENABLED = True
    GRID_SIZE = 10

    def __init__(self, length=100, thickness=10, arrow_type="cylinder", arrow_pos="end", base_color=QColor(200, 50, 50), opacity=100):
        super().__init__()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.length = length
        self.thickness = thickness
        self.arrow_type = arrow_type # "none", "flat", "cylinder"
        self.arrow_pos = arrow_pos # "end", "start", "both"
        self.base_color = base_color
        self.opacity_val = opacity
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.rot_z = 0.0

        import uuid
        self.item_id = str(uuid.uuid4())
        self.pierce_peer = None
        self.is_front_half = False
        self.logical_center = None
        self.logical_length = self.length
        self._is_syncing = False

        from PyQt6.QtWidgets import QGraphicsLineItem

        self.poly_items = []

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
        if self.length <= 0: return faces

        al = min(self.thickness * 3, self.logical_length / 2 if self.arrow_pos == "both" else self.logical_length)
        draw_start = self.arrow_pos in ["start", "both"]
        draw_end = self.arrow_pos in ["end", "both"]

        start_al = al if draw_start else 0
        end_al = al if draw_end else 0

        ll = self.length - start_al - end_al

        if self.arrow_type == "flat":
            if ll > 0: faces.extend(generate_box(ll, self.thickness, max(1, self.thickness * 0.2), -self.length/2 + start_al))
            if end_al > 0: faces.extend(generate_flat_arrow(self.thickness * 2.5, end_al, max(1, self.thickness * 0.2), -self.length/2 + start_al + ll))
            if start_al > 0:
                start_faces = generate_flat_arrow(self.thickness * 2.5, start_al, max(1, self.thickness * 0.2), -start_al)
                # Mirror arrow for start
                start_faces = [[(-x - self.length/2, y, z) for x, y, z in f] for f in start_faces]
                faces.extend(start_faces)
        elif self.arrow_type == "cylinder":
            if ll > 0: faces.extend(generate_cylinder(self.thickness / 2, ll, segments=36, offset_x=-self.length/2 + start_al))
            if end_al > 0: faces.extend(generate_cone(self.thickness * 1.2, end_al, segments=36, offset_x=-self.length/2 + start_al + ll))
            if start_al > 0:
                start_faces = generate_cone(self.thickness * 1.2, start_al, segments=36, offset_x=-start_al)
                # Mirror cone for start
                start_faces = [[(-x - self.length/2, y, z) for x, y, z in f] for f in start_faces]
                faces.extend(start_faces)
        else: # none
            faces.extend(generate_cylinder(self.thickness / 2, self.length, segments=36, offset_x=-self.length/2))

        return faces

    def update_geometry(self, length=None, thickness=None, arrow_type=None, arrow_pos=None, base_color=None, opacity=None, rot_x=None, rot_y=None, rot_z=None):
        self.prepareGeometryChange()

        if length is not None: self.length = max(1, length)
        if thickness is not None: self.thickness = max(1, thickness)
        if arrow_type is not None: self.arrow_type = arrow_type
        if arrow_pos is not None: self.arrow_pos = arrow_pos
        if base_color is not None: self.base_color = base_color
        if opacity is not None: self.opacity_val = max(10, min(100, opacity))
        if rot_x is not None: self.rot_x = rot_x
        if rot_y is not None: self.rot_y = rot_y
        if rot_z is not None: self.rot_z = rot_z

        self.setOpacity(self.opacity_val / 100.0)
        faces = self._generate_mesh()

        visible_faces = []
        for face in faces:
            rot_face = [rotate_3d(x, y, z, self.rot_x, self.rot_y, self.rot_z) for x, y, z in face]
            nx, ny, nz = compute_normal(rot_face)

            cx = sum(v[0] for v in rot_face) / len(rot_face)
            cy = sum(v[1] for v in rot_face) / len(rot_face)
            cz = sum(v[2] for v in rot_face) / len(rot_face)
            depth = cx + cy + cz

            lx, ly, lz = 0.5, 1.0, 1.5
            ll = math.sqrt(lx*lx + ly*ly + lz*lz)
            dot = (nx*lx + ny*ly + nz*lz) / ll
            factor = 0.4 + 0.6 * (0.5 + 0.5 * dot)

            poly = QPolygonF()
            for rx, ry, rz in rot_face:
                sx, sy = project_iso(rx, ry, rz)
                poly.append(QPointF(sx, sy))

            visible_faces.append({'poly': poly, 'depth': depth, 'factor': factor})

        visible_faces.sort(key=lambda f: f['depth'])

        # Clean up old polygons completely to prevent rendering artifacts during dragging
        for p in self.poly_items:
            p.setParentItem(None)
            if self.scene():
                self.scene().removeItem(p)
        self.poly_items.clear()

        sel_pen = QPen(Qt.GlobalColor.blue, 1.5, Qt.PenStyle.DashLine)
        norm_pen = QPen(Qt.GlobalColor.black, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

        for vf in visible_faces:
            item = QGraphicsPolygonItem()
            item.setPolygon(vf['poly'])
            r = min(255, max(0, int(self.base_color.red() * vf['factor'])))
            g = min(255, max(0, int(self.base_color.green() * vf['factor'])))
            b = min(255, max(0, int(self.base_color.blue() * vf['factor'])))
            brush_color = QColor(r, g, b)
            item.setBrush(QBrush(brush_color))
            if self.isSelected():
                item.setPen(sel_pen)
            else:
                if self.arrow_type == "flat" or vf.get('is_flat_part', False):
                    item.setPen(norm_pen)
                else:
                    item.setPen(QPen(brush_color, 1.0))
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
            new_pos = value
            is_syncing = getattr(self, '_is_syncing', False)
            if self.SNAP_ENABLED and not is_syncing:
                sx = new_pos.x()
                sy = new_pos.y()
                import math
                c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
                iso_x = (sx / c + sy / s) / 2
                iso_y = (sy / s - sx / c) / 2
                iso_x = round(iso_x / self.GRID_SIZE) * self.GRID_SIZE
                iso_y = round(iso_y / self.GRID_SIZE) * self.GRID_SIZE
                snap_sx = (iso_x - iso_y) * c
                snap_sy = (iso_x + iso_y) * s
                new_pos = QPointF(snap_sx, snap_sy)

            if self.pierce_peer and not is_syncing:
                self._is_syncing = True
                
                # Calculate logical center from new_pos
                rx, ry, rz = rotate_3d(self.logical_length / 4 * (1 if self.is_front_half else -1), 0, 0, self.rot_x, self.rot_y, self.rot_z)
                sx, sy = project_iso(rx, ry, rz)
                
                center_x = new_pos.x() - sx
                center_y = new_pos.y() - sy
                self.logical_center = QPointF(center_x, center_y)
                self.pierce_peer.logical_center = self.logical_center
                
                # Update peer's pos
                rx_p, ry_p, rz_p = rotate_3d(self.logical_length / 4 * (1 if self.pierce_peer.is_front_half else -1), 0, 0, self.rot_x, self.rot_y, self.rot_z)
                sx_p, sy_p = project_iso(rx_p, ry_p, rz_p)
                
                self.pierce_peer.setPos(center_x + sx_p, center_y + sy_p)
                self._is_syncing = False

            return new_pos
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_geometry()
        return super().itemChange(change, value)

    def clone(self):
        new_item = IsoLineItem(length=self.length, thickness=self.thickness, arrow_type=self.arrow_type, arrow_pos=self.arrow_pos, base_color=self.base_color, opacity=self.opacity_val)
        new_item.rot_x = self.rot_x
        new_item.rot_y = self.rot_y
        new_item.rot_z = self.rot_z
        new_item.update_geometry()
        return new_item


    def to_dict(self):
        d = {
            'type': 'IsoLineItem',
            'item_id': self.item_id,
            'pos': {'x': self.pos().x(), 'y': self.pos().y()},
            'zValue': self.zValue(),
            'length': self.length, 'thickness': self.thickness,
            'arrow_type': self.arrow_type, 'arrow_pos': self.arrow_pos,
            'base_color': self.base_color.name(),
            'opacity': self.opacity_val,
            'rot_x': self.rot_x, 'rot_y': self.rot_y, 'rot_z': self.rot_z
        }
        if self.pierce_peer:
            d['pierce_peer_id'] = self.pierce_peer.item_id
            d['is_front_half'] = self.is_front_half
            if self.logical_center:
                d['logical_center'] = {'x': self.logical_center.x(), 'y': self.logical_center.y()}
            d['logical_length'] = self.logical_length
        return d
