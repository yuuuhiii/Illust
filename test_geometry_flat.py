from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QMouseEvent, QPainter, QPen
from PyQt6.QtCore import QPointF, Qt, QEvent, QPoint
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

window.combo_arrow_type.setCurrentIndex(window.combo_arrow_type.findData("flat"))
window.combo_arrow_pos.setCurrentIndex(window.combo_arrow_pos.findData("both"))

view = window.canvas

p1 = QPoint(300, 300)
p2 = QPoint(500, 400)

event_press = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(p1), QPointF(p1), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
view.mousePressEvent(event_press)

event_move = QMouseEvent(QEvent.Type.MouseMove, QPointF(p2), QPointF(p2), Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
view.mouseMoveEvent(event_move)

event_release = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(p2), QPointF(p2), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
view.mouseReleaseEvent(event_release)

app.processEvents()

# Try unselecting
view.scene.clearSelection()
app.processEvents()

screenshot = view.grab()
screenshot.save("/tmp/app_screenshot_flat.png")
