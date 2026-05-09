class ToolManager:
    def __init__(self, view):
        self.view = view
        self.current_tool = None
    def set_tool(self, tool): 
        self.current_tool = tool
    def mousePressEvent(self, event):
        if self.current_tool: self.current_tool.mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self.current_tool: self.current_tool.mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if self.current_tool: self.current_tool.mouseReleaseEvent(event)