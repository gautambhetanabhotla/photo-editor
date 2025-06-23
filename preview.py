from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PySide6.QtGui import QPainter, QPainter, QKeySequence, QShortcut, QMouseEvent, QPen, QBrush
from PySide6.QtCore import Qt, Signal

from layers import Layer

class PreviewWindow(QGraphicsView):
    layerClicked = Signal(Layer, bool)

    def __init__(self):
        super().__init__()
        self.scene: QGraphicsScene = QGraphicsScene()
        self.setScene(self.scene)
        self.layers = []  # Store reference to layers for click detection
        
        # Enable zooming with mouse wheel
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Add zoom shortcuts
        self.zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+="), self)
        self.zoom_in_shortcut.activated.connect(self.zoomIn)
        
        self.zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoom_out_shortcut.activated.connect(self.zoomOut)
        
        # Also handle Ctrl+0 for fit to window
        self.fit_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        self.fit_shortcut.activated.connect(self.fitToWindow)

        self.reset_zoom_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.reset_zoom_shortcut.activated.connect(self.resetZoom)
    
    def zoomIn(self):
        self.scale(1.25, 1.25)
    
    def zoomOut(self):
        self.scale(0.8, 0.8)
    
    def resetZoom(self):
        self.resetTransform()

    def fitToWindow(self):
        if self.scene.sceneRect().isValid():
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert mouse position to scene coordinates
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # Check if Ctrl is pressed
            ctrl_pressed = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            
            # Find topmost layer containing the click position
            # Check layers in reverse order (top to bottom)
            for layer in reversed(self.layers):
                if layer.visible and layer.containsPoint(scene_pos):
                    self.layerClicked.emit(layer, ctrl_pressed)
                    break
            else:
                self.layerClicked.emit(None, False)
        
        super().mousePressEvent(event)
    
    def render(self, layers: list[Layer]):
        # Store layers reference for click detection
        self.layers = layers
        
        # Clear the scene
        self.scene.clear()
        # self.scene = QGraphicsScene()
        # self.setScene(self.scene)

        # Calculate bounding rect for all layers
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')   

        for layer in layers:
            if layer.visible:
                item = QGraphicsPixmapItem(layer.pixmap)
                item.setPos(layer.position['x'], layer.position['y'])
                item.setOpacity(layer.opacity)
                self.scene.addItem(item)

                x = layer.position['x']
                y = layer.position['y']
                w = layer.pixmap.width()
                h = layer.pixmap.height()

                if layer.selected:
                    # Draw a selection rectangle around the layer
                    selection_rect = QGraphicsRectItem(x, y, w, h)
                    selection_rect.setPen(QPen(Qt.GlobalColor.blue, 2))
                    selection_rect.setBrush(QBrush(Qt.GlobalColor.transparent))
                    self.scene.addItem(selection_rect)
                
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x + w)
                max_y = max(max_y, y + h)
        
        if min_x != float('inf'):
            self.scene.setSceneRect(min_x, min_y, max_x - min_x, max_y - min_y)