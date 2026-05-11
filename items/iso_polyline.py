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

        self.points = points if points else [] # list of QPointF in 3D grid space (X, Y) where Z=0
        self.thickness = thickness
        self.base_color = base_color
        self.opacity_val = opacity

        self.path_item = QGraphicsPathItem()
        self.path_item.setParentItem(self)

        self.update_geometry()

    def update_geometry(self, points=None, thickness=None, base_color=None, opacity=None):
        self.prepareGeometryChange()

        if points is not None: self.points = points
        if thickness is not None: self.thickness = max(1, thickness)
        if base_color is not None: self.base_color = base_color
        if opacity is not None: self.opacity_val = max(10, min(100, opacity))

        self.setOpacity(self.opacity_val / 100.0)

        if not self.points or len(self.points) < 2:
            self.path_item.setPath(QPainterPath())
            return

        path = QPainterPath()

        for i, pt in enumerate(self.points):
            # Project from 3D flat grid to isometric 2D screen
            sx, sy = project_iso(pt.x(), pt.y(), 0)
            if i == 0:
                path.moveTo(sx, sy)
            else:
                path.lineTo(sx, sy)

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

    def clone(self):
        new_item = IsoPolylineItem(points=list(self.points), thickness=self.thickness, base_color=self.base_color, opacity=self.opacity_val)
        new_item.update_geometry()
        return new_item
