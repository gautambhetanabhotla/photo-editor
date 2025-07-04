from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PySide6.QtGui import QPainter, QPainter, QKeySequence, QShortcut, QMouseEvent, QPen, QBrush
from PySide6.QtCore import Qt, Signal, QPointF

from layers import Layer

class PreviewWindow(QGraphicsView):
    layerClicked = Signal(Layer, bool)
    layerMoved = Signal()  # Signal to notify when layers have been moved

    def __init__(self):
        super().__init__()
        self.scene: QGraphicsScene = QGraphicsScene()
        self.setScene(self.scene)
        self.layers = []  # Store reference to layers for click detection
        
        # Drag state variables
        self.isDragging = False
        self.dragStartPosition = QPointF()
        self.selectedLayersStartPositions = {}  # Store original positions of selected layers
        
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
            clicked_layer = None
            for layer in reversed(self.layers):
                if layer.visible and layer.containsPoint(scene_pos):
                    clicked_layer = layer
                    break
            
            # If we clicked on a selected layer, prepare for dragging
            if clicked_layer and clicked_layer.selected:
                self.isDragging = True
                self.dragStartPosition = scene_pos
                # Store original positions of all selected layers
                self.selectedLayersStartPositions = {}
                for layer in self.layers:
                    if layer.selected:
                        self.selectedLayersStartPositions[layer] = {
                            'x': layer.position['x'],
                            'y': layer.position['y']
                        }
                # Disable rubber band drag during layer dragging
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
            else:
                # Handle layer selection
                self.layerClicked.emit(clicked_layer, ctrl_pressed)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.isDragging and event.buttons() & Qt.MouseButton.LeftButton:
            # Calculate the drag offset
            current_pos = self.mapToScene(event.position().toPoint())
            offset = current_pos - self.dragStartPosition
            
            # Move all selected layers by the offset
            for layer, start_pos in self.selectedLayersStartPositions.items():
                new_pos = QPointF(start_pos['x'] + offset.x(), start_pos['y'] + offset.y())
                layer.setPosition(new_pos.x(), new_pos.y())
            
            # Re-render the preview to show the updated positions
            self.render(self.layers)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.isDragging:
            self.isDragging = False
            self.selectedLayersStartPositions.clear()
            # Re-enable rubber band drag
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            # Emit signal to notify that layers have been moved
            self.layerMoved.emit()
        
        super().mouseReleaseEvent(event)
    
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