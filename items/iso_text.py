import math
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPathItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QPainterPath, QTransform
from PyQt6.QtCore import Qt, QPointF
from items.math3d import project_iso

class IsoTextItem(QGraphicsItemGroup):
    SNAP_ENABLED = True
    GRID_SIZE = 10

    def __init__(self, text="Text", font_size=30, plane="XY", base_color=QColor(0, 0, 0), opacity=100):
        super().__init__()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.text = text
        self.font_size = font_size
        self.plane = plane # "Screen", "XY", "YZ", "XZ"
        self.base_color = base_color
        self.opacity_val = opacity

        self.path_item = QGraphicsPathItem()
        self.path_item.setParentItem(self)

        self.update_geometry()

    def update_geometry(self, text=None, font_size=None, plane=None, base_color=None, opacity=None):
        self.prepareGeometryChange()

        if text is not None: self.text = text
        if font_size is not None: self.font_size = max(5, font_size)
        if plane is not None: self.plane = plane
        if base_color is not None: self.base_color = base_color
        if opacity is not None: self.opacity_val = max(10, min(100, opacity))

        self.setOpacity(self.opacity_val / 100.0)

        if not self.text:
            self.path_item.setPath(QPainterPath())
            return

        font = QFont("Arial", self.font_size)
        font.setStyleStrategy(QFont.StyleStrategy.ForceOutline)

        path = QPainterPath()
        path.addText(0, 0, font, self.text)

        br = path.boundingRect()
        cx = br.center().x()
        cy = br.center().y()

        # Center the path
        center_transform = QTransform().translate(-cx, -cy)
        centered_path = center_transform.map(path)

        angle = math.radians(30)
        c, s = math.cos(angle), math.sin(angle)

        iso_transform = QTransform()

        if self.plane == "Screen":
            # No projection
            iso_transform = QTransform()
        elif self.plane == "XY": # Floor
            # px -> X, py -> Y
            # sx = (X - Y)*c = px*c - py*c
            # sy = (X + Y)*s - Z = px*s + py*s
            # QTransform(m11, m12, m21, m22, dx, dy)
            # x' = m11*x + m21*y + dx
            # y' = m12*x + m22*y + dy
            # Therefore: m11=c, m12=s, m21=-c, m22=s
            iso_transform = QTransform(c, s, -c, s, 0, 0)
        elif self.plane == "XZ": # Right Wall
            # px -> X, py -> -Z
            # sx = X*c = px*c
            # sy = X*s - Z = px*s - (-py) = px*s + py
            # m11=c, m12=s, m21=0, m22=1
            iso_transform = QTransform(c, s, 0, 1, 0, 0)
        elif self.plane == "YZ": # Left Wall
            # px -> Y, py -> -Z
            # sx = -Y*c = -px*c
            # sy = Y*s - Z = px*s - (-py) = px*s + py
            # m11=-c, m12=s, m21=0, m22=1
            iso_transform = QTransform(-c, s, 0, 1, 0, 0)

        mapped_path = iso_transform.map(centered_path)
        self.path_item.setPath(mapped_path)

        # Draw with brush and pen to fix the fill and visibility issues
        self.path_item.setBrush(QBrush(self.base_color))

        # Add an outline so text is clear. Same color as base or slightly darker,
        # but let's use the base color for the fill and a thin solid outline.
        pen = QPen(self.base_color, 1.0)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.path_item.setPen(pen)

        if self.isSelected():
            sel_pen = QPen(Qt.GlobalColor.blue, 2.0, Qt.PenStyle.DashLine)
            # We can draw the selection outline over it, or just change the pen.
            # Usually we add a bounding box for selection, but changing pen is fine.
            self.path_item.setPen(sel_pen)

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
