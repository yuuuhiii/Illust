from PyQt6.QtWidgets import QApplication
import sys
from PyQt6.QtCore import QPointF

app = QApplication(sys.argv)
from ui.main_window import MainWindow

win = MainWindow()
win.show()

from items.iso_shape import IsoShapeItem
from items.iso_text import IsoTextItem

# Add items directly to scene
shape = IsoShapeItem(shape_type="circle", size=200)
win.canvas.add_block(shape, QPointF(100, 100))

text = IsoTextItem(text="Test 3D", plane="XY")
win.canvas.add_block(text, QPointF(200, 200))

print("Integration test passed.")
