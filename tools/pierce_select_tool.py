from tools.base_tool import BaseTool
from items.iso_block import IsoBlockItem
from items.iso_shape import IsoShapeItem
from PyQt6.QtWidgets import QGraphicsItem, QMessageBox
from PyQt6.QtCore import Qt

class PierceSelectTool(BaseTool):
    def __init__(self, view, piercing_line):
        super().__init__(view)
        self.piercing_line = piercing_line
        
        # Determine front and back from the linked pair
        if self.piercing_line.is_front_half:
            self.front_line = self.piercing_line
            self.back_line = self.piercing_line.pierce_peer
        else:
            self.front_line = self.piercing_line.pierce_peer
            self.back_line = self.piercing_line
            
        # Give user a brief instruction (could be status bar, but for now just visual)
        if hasattr(self.view.window(), 'statusBar'):
            self.view.window().statusBar().showMessage("貫通させたい図形をクリックしてください。終了するにはEscキーを押すか、何もない場所をクリックします。")

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
            
        pos = self.view.mapToScene(event.pos())
        items = self.view.scene.items(pos)
        
        target = None
        for item in items:
            # Skip the lines themselves
            if item == self.front_line or item == self.back_line:
                continue
            if isinstance(item, (IsoBlockItem, IsoShapeItem)):
                target = item
                break
                
        if target:
            # Reorder Z-index
            if self.front_line in self.view.block_list and self.back_line in self.view.block_list and target in self.view.block_list:
                self.view.block_list.remove(target)
                
                # Insert target just before front_line (so it is after back_line and before front_line)
                front_idx = self.view.block_list.index(self.front_line)
                self.view.block_list.insert(front_idx, target)
                
                self.view.update_z_values()
                if hasattr(self.view.window(), 'save_state'):
                    self.view.window().save_state()
                    
                if hasattr(self.view.window(), 'statusBar'):
                    self.view.window().statusBar().showMessage("対象を図形間に挟み込みました。続けてクリックするか、Escキーで終了します。")
        else:
            # Clicked empty space -> exit tool
            self.exit_tool()
            
        event.accept()

    def mouseMoveEvent(self, event):
        # We can change cursor over valid targets if we want
        pass
        
    def exit_tool(self):
        from tools.select_tool import SelectTool
        self.view.tool_manager.set_tool(SelectTool(self.view))
        if hasattr(self.view.window(), 'statusBar'):
            self.view.window().statusBar().clearMessage()
