from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsItem
from PyQt6.QtCore import QPointF
import math

class IsoGroupItem(QGraphicsItemGroup):
    SNAP_ENABLED = True
    GRID_SIZE = 10

    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            if self.SNAP_ENABLED:
                new_pos = value
                sx = new_pos.x()
                sy = new_pos.y()
                c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
                # Inverse projection assuming z=0
                iso_x = (sx / c + sy / s) / 2
                iso_y = (sy / s - sx / c) / 2

                iso_x = round(iso_x / self.GRID_SIZE) * self.GRID_SIZE
                iso_y = round(iso_y / self.GRID_SIZE) * self.GRID_SIZE

                snap_sx = (iso_x - iso_y) * c
                snap_sy = (iso_x + iso_y) * s
                return QPointF(snap_sx, snap_sy)
        return super().itemChange(change, value)

    def clone(self):
        new_group = IsoGroupItem()
        for child in self.childItems():
            if hasattr(child, 'clone'):
                new_child = child.clone()
                new_group.addToGroup(new_child)
                new_child.setPos(child.pos())
                new_child.setZValue(child.zValue())
        return new_group

    def to_dict(self):
        children_data = []
        # Sort children by zValue to maintain order when saving/loading
        sorted_children = sorted(self.childItems(), key=lambda c: c.zValue())
        for child in sorted_children:
            if hasattr(child, 'to_dict'):
                children_data.append(child.to_dict())

        return {
            'type': 'IsoGroupItem',
            'pos': {'x': self.pos().x(), 'y': self.pos().y()},
            'zValue': self.zValue(),
            'children': children_data
        }
