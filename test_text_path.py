from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsPathItem
from PyQt6.QtGui import QPainterPath, QFont, QTransform, QColor, QBrush, QPen
from PyQt6.QtCore import Qt
import math
import sys

app = QApplication(sys.argv)

path = QPainterPath()
font = QFont("Arial", 45)
path.addText(0, 0, font, "TbCo薄膜")

angle = math.radians(30)
c, s = math.cos(angle), math.sin(angle)

# XY
t = QTransform(c, s, -c, s, 0, 0)
mapped_path = t.map(path)

item = QGraphicsPathItem(mapped_path)
item.setBrush(QBrush(QColor("blue")))
item.setPen(QPen(QColor("black"), 1))

scene = QGraphicsScene()
scene.addItem(item)
view = QGraphicsView(scene)
# view.show() # Can't show in offscreen

print("Transform applied successfully.")
