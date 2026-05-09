class BaseTool:
    def __init__(self, view):
        self.view = view
        self.scene = view.scene
    def mousePressEvent(self, event): pass
    def mouseMoveEvent(self, event): pass
    def mouseReleaseEvent(self, event): pass