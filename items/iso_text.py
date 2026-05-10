import math
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF, QFont, QPainterPath
from PyQt6.QtCore import Qt, QPointF
from items.math3d import rotate_3d, project_iso, compute_normal

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

        self.poly_items = []
        self.update_geometry()

    def update_geometry(self, text=None, font_size=None, plane=None, base_color=None, opacity=None):
        self.prepareGeometryChange()

        if text is not None: self.text = text
        if font_size is not None: self.font_size = max(5, font_size)
        if plane is not None: self.plane = plane
        if base_color is not None: self.base_color = base_color
        if opacity is not None: self.opacity_val = max(10, min(100, opacity))

        self.setOpacity(self.opacity_val / 100.0)

        for p in self.poly_items:
            p.setParentItem(None)
            if self.scene():
                self.scene().removeItem(p)
        self.poly_items.clear()

        if not self.text:
            return

        font = QFont("Arial", self.font_size)
        font.setStyleStrategy(QFont.StyleStrategy.ForceOutline)

        path = QPainterPath()
        # Add text to path. (0,0) is baseline start.
        path.addText(0, 0, font, self.text)

        # We can extract polygons from the painter path
        polygons = path.toSubpathPolygons()

        # We need to map these 2D polygons into our 3D space depending on the plane
        # In our QPainterPath: X goes right, Y goes down (but text baseline is at 0, so text is mainly negative Y).
        # We will center the text roughly.
        br = path.boundingRect()
        cx = br.center().x()
        cy = br.center().y()

        sel_pen = QPen(Qt.GlobalColor.blue, 2.0, Qt.PenStyle.DashLine) if self.isSelected() else QPen(Qt.PenStyle.NoPen)

        for poly2d in polygons:
            mapped_poly = QPolygonF()
            for i in range(poly2d.count()):
                pt = poly2d.at(i)
                px = pt.x() - cx
                py = pt.y() - cy

                # Default 3D coordinates
                x, y, z = 0, 0, 0

                if self.plane == "Screen":
                    # Just flat on screen, no 3D projection
                    mapped_poly.append(QPointF(px, py))
                    continue
                elif self.plane == "XY": # Floor plane
                    # X axis maps to px, Y axis maps to py
                    x, y, z = px, py, 0
                elif self.plane == "YZ": # Right wall
                    # Y axis maps to px, Z axis maps to py
                    x, y, z = 0, px, py
                elif self.plane == "XZ": # Left wall
                    # X axis maps to px, Z axis maps to py
                    x, y, z = px, 0, py

                # Apply isometric projection
                sx, sy = project_iso(x, y, z)
                mapped_poly.append(QPointF(sx, sy))

            item = QGraphicsPolygonItem()
            item.setPolygon(mapped_poly)
            item.setBrush(QBrush(self.base_color))
            item.setPen(sel_pen)
            item.setParentItem(self)
            self.poly_items.append(item)

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
