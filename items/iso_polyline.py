from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPathItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QPainterPath
from PyQt6.QtCore import Qt, QPointF
from items.math3d import project_iso

class IsoPolylineItem(QGraphicsItemGroup):
    SNAP_ENABLED = True
    GRID_SIZE = 10

    def __init__(self, points=None, thickness=2, base_color=QColor(0, 0, 0), opacity=100):
        super().__init__()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.points = points if points else []
        self.thickness = thickness
        self.base_color = base_color
        self.opacity_val = opacity

        self.path_item = QGraphicsPathItem()
        self.path_item.setParentItem(self)

        self.control_points = []
        self.update_geometry()

    def update_geometry(self, points=None, thickness=None, base_color=None, opacity=None):
        self.prepareGeometryChange()

        if points is not None: self.points = points
        if thickness is not None: self.thickness = max(1, thickness)
        if base_color is not None: self.base_color = base_color
        if opacity is not None: self.opacity_val = max(10, min(100, opacity))

        self.setOpacity(self.opacity_val / 100.0)

        # Clear old control points
        for cp in self.control_points:
            if self.scene():
                self.scene().removeItem(cp)
        self.control_points.clear()

        if not self.points or len(self.points) < 2:
            self.path_item.setPath(QPainterPath())
            return

        path = QPainterPath()

        for i, pt in enumerate(self.points):
            sx, sy = project_iso(pt.x(), pt.y(), 0)
            if i == 0:
                path.moveTo(sx, sy)
            else:
                path.lineTo(sx, sy)

            if self.isSelected():
                from PyQt6.QtWidgets import QGraphicsEllipseItem
                from PyQt6.QtGui import QBrush, QColor

                # Small circular handle for each node
                cp_size = 8
                cp = QGraphicsEllipseItem(-cp_size/2, -cp_size/2, cp_size, cp_size)
                cp.setPos(sx, sy)
                cp.setBrush(QBrush(QColor(255, 255, 255)))
                cp.setPen(QPen(QColor(0, 0, 255), 1.5))
                cp.setParentItem(self)
                cp.setData(0, "control_point")
                cp.setData(1, i) # Store index of point
                self.control_points.append(cp)

        self.path_item.setPath(path)

        pen = QPen(self.base_color, self.thickness)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        if self.isSelected():
            pen.setStyle(Qt.PenStyle.DashLine)

        self.path_item.setPen(pen)

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


    def mousePressEvent(self, event):
        # Check if clicking on a control point
        for cp in self.control_points:
            if cp.contains(cp.mapFromParent(event.pos())):
                self.dragging_index = cp.data(1)
                event.accept()
                return
        self.dragging_index = -1
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if hasattr(self, 'dragging_index') and self.dragging_index >= 0:
            local_pos = event.pos()

            # Inverse projection
            import math
            angle = math.radians(30)
            c, s = math.cos(angle), math.sin(angle)
            A = local_pos.x() / c
            B = local_pos.y() / s
            X = (A + B) / 2.0
            Y = (B - A) / 2.0

            if self.SNAP_ENABLED:
                X = round(X / self.GRID_SIZE) * self.GRID_SIZE
                Y = round(Y / self.GRID_SIZE) * self.GRID_SIZE

            self.points[self.dragging_index] = QPointF(X, Y)
            self.update_geometry()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'dragging_index') and self.dragging_index >= 0:
            self.dragging_index = -1
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Click on existing CP to delete it
        for cp in self.control_points:
            if cp.contains(cp.mapFromParent(event.pos())):
                idx = cp.data(1)
                if len(self.points) > 2:
                    self.points.pop(idx)
                    self.update_geometry()
                event.accept()
                return

        # Click on segment to add point
        # A simple approximation: if close to path, inject point
        if self.path_item.contains(event.pos()):
            local_pos = event.pos()
            import math
            angle = math.radians(30)
            c, s = math.cos(angle), math.sin(angle)
            A = local_pos.x() / c
            B = local_pos.y() / s
            X = (A + B) / 2.0
            Y = (B - A) / 2.0

            if self.SNAP_ENABLED:
                X = round(X / self.GRID_SIZE) * self.GRID_SIZE
                Y = round(Y / self.GRID_SIZE) * self.GRID_SIZE

            new_pt = QPointF(X, Y)

            # Find best segment to insert to (closest distance)
            best_idx = 1
            min_dist = float('inf')

            for i in range(len(self.points)-1):
                p1 = self.points[i]
                p2 = self.points[i+1]
                # distance from new_pt to line segment p1-p2
                # cross product approximation
                dist = abs((p2.y()-p1.y())*new_pt.x() - (p2.x()-p1.x())*new_pt.y() + p2.x()*p1.y() - p2.y()*p1.x()) / (math.hypot(p2.y()-p1.y(), p2.x()-p1.x()) + 0.001)
                if dist < min_dist:
                    min_dist = dist
                    best_idx = i + 1

            self.points.insert(best_idx, new_pt)
            self.update_geometry()
            event.accept()
            return

        super().mouseDoubleClickEvent(event)
    def clone(self):
        new_item = IsoPolylineItem(points=list(self.points), thickness=self.thickness, base_color=self.base_color, opacity=self.opacity_val)
        new_item.update_geometry()
        return new_item


    def to_dict(self):
        return {
            'type': 'IsoPolylineItem',
            'pos': {'x': self.pos().x(), 'y': self.pos().y()},
            'zValue': self.zValue(),
            'points': [{'x': p.x(), 'y': p.y()} for p in self.points],
            'thickness': self.thickness,
            'base_color': self.base_color.name(),
            'opacity': self.opacity_val
        }
