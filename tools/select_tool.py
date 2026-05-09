from PyQt6.QtWidgets import QGraphicsView
from tools.base_tool import BaseTool

class SelectTool(BaseTool):
    def __init__(self, view):
        super().__init__(view)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)