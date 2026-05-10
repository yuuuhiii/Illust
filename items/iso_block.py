import math
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF

class IsoBlockItem(QGraphicsItemGroup):
    SNAP_ENABLED = True
    GRID_SIZE = 10

    def __init__(self, w=150, d=100, h=40, base_color=QColor(200, 200, 210), opacity=100):
        super().__init__()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.w, self.d, self.h = w, d, h
        self.base_color = base_color
        self.opacity_val = opacity

        self.top_item = QGraphicsPolygonItem()
        self.right_item = QGraphicsPolygonItem()
        self.left_item = QGraphicsPolygonItem()

        pen = QPen(Qt.GlobalColor.black, 1.5)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        for item in [self.top_item, self.right_item, self.left_item]:
            item.setPen(pen)
            self.addToGroup(item)

        self.update_geometry()

    def update_geometry(self, w=None, d=None, h=None, base_color=None, opacity=None):
        self.prepareGeometryChange()

        if w is not None: self.w = w
        if d is not None: self.d = d
        if h is not None: self.h = h
        if base_color is not None: self.base_color = base_color
        if opacity is not None: 
            self.opacity_val = opacity
            self.setOpacity(self.opacity_val / 100.0)

        angle = math.radians(30)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        v_front_top = QPointF(0, 0)
        v_right_top = QPointF(self.w * cos_a, -self.w * sin_a)
        v_left_top = QPointF(-self.d * cos_a, -self.d * sin_a)
        v_back_top = QPointF((self.w - self.d) * cos_a, -(self.w + self.d) * sin_a)
        v_front_bottom = QPointF(0, self.h)
        v_right_bottom = QPointF(self.w * cos_a, -self.w * sin_a + self.h)
        v_left_bottom = QPointF(-self.d * cos_a, -self.d * sin_a + self.h)

        self.top_item.setPolygon(QPolygonF([v_front_top, v_right_top, v_back_top, v_left_top]))
        self.right_item.setPolygon(QPolygonF([v_front_top, v_right_top, v_right_bottom, v_front_bottom]))
        self.left_item.setPolygon(QPolygonF([v_front_top, v_left_top, v_left_bottom, v_front_bottom]))

        self.top_item.setBrush(QBrush(self.base_color.lighter(110)))
        self.right_item.setBrush(QBrush(self.base_color.darker(130)))
        self.left_item.setBrush(QBrush(self.base_color.darker(110)))

        if self.isSelected():
            sel_pen = QPen(Qt.GlobalColor.blue, 2.0, Qt.PenStyle.DashLine)
            self.top_item.setPen(sel_pen)
            self.right_item.setPen(sel_pen)
            self.left_item.setPen(sel_pen)
        else:
            norm_pen = QPen(Qt.GlobalColor.black, 1.5)
            norm_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            self.top_item.setPen(norm_pen)
            self.right_item.setPen(norm_pen)
            self.left_item.setPen(norm_pen)

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            if IsoBlockItem.SNAP_ENABLED:
                new_pos = value
                x = round(new_pos.x() / IsoBlockItem.GRID_SIZE) * IsoBlockItem.GRID_SIZE
                y = round(new_pos.y() / IsoBlockItem.GRID_SIZE) * IsoBlockItem.GRID_SIZE
                return QPointF(x, y)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_geometry()
        return super().itemChange(change, value)