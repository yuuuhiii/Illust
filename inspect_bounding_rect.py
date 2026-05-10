from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF, Qt, QEvent, QPoint
from PyQt6.QtGui import QMouseEvent
import sys

app = QApplication(sys.argv)
from ui.main_window import MainWindow

window = MainWindow()
window.show()
app.processEvents()

from tools.iso_line_tool import DrawIsoLineTool
tool_manager = window.canvas.tool_manager
line_tool = DrawIsoLineTool(window.canvas, window.get_line_props)
tool_manager.set_tool(line_tool)

view = window.canvas

p1 = QPoint(300, 300)
p2 = QPoint(500, 400)

event_press = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(p1), QPointF(p1), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
view.mousePressEvent(event_press)

event_move = QMouseEvent(QEvent.Type.MouseMove, QPointF(p2), QPointF(p2), Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
view.mouseMoveEvent(event_move)

app.processEvents()

item = tool_manager.current_tool.preview_item
print("Preview item actual pos:", item.pos())
print("Preview item boundingRect:", item.boundingRect())
print("Preview item sceneBoundingRect:", item.sceneBoundingRect())
for child in item.childItems():
    if child.isVisible():
        print("Child pos:", child.pos(), "scenePos:", child.scenePos(), "rect:", child.boundingRect())
