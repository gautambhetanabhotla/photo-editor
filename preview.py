from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtGui import QPainter, QPainter, QKeySequence, QShortcut, QMouseEvent, QPen, QBrush
from PySide6.QtCore import Qt, Signal, QPointF, QRectF

from layers import Layer

class TransformHandle(QGraphicsEllipseItem):
    """A circular handle for transforming layers"""
    def __init__(self, handle_type: str, parent=None):
        super().__init__(parent)
        self.handle_type = handle_type  # 'corner', 'edge_h', 'edge_v'
        self.setRect(-4, -4, 8, 8)  # 8x8 pixel circle
        self.setPen(QPen(Qt.GlobalColor.blue, 2))
        self.setBrush(QBrush(Qt.GlobalColor.white))
        self.setData(0, "ui_element")
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

class PreviewWindow(QGraphicsView):
    layerClicked = Signal(Layer, bool)
    layerTransformed = Signal()  # Signal to notify when layers have been moved

    def __init__(self):
        super().__init__()
        self.scene: QGraphicsScene = QGraphicsScene()
        self.setScene(self.scene)
        self.layers = []  # Store reference to layers for click detection
        
        # Drag state variables
        self.isDragging = False
        self.dragStartPosition = QPointF()
        self.selectedLayersStartPositions = {}  # Store original positions of selected layers
        
        # Transform state variables
        self.isTransforming = False
        self.transformHandle = None  # Currently dragged transform handle
        self.transformHandleType = ""  # Store handle type to avoid accessing deleted object
        self.transformStartPosition = QPointF()
        self.selectedLayersStartScales = {}  # Store original scales of selected layers
        self.transformBounds = QRectF()  # Bounding rect of selected layers
        
        # Zoom tracking
        self.currentZoom = 1.0  # Track current zoom level
        
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
        zoom_factor = 1.25
        self.scale(zoom_factor, zoom_factor)
        self.currentZoom *= zoom_factor
        self.refreshTransformHandles()  # Refresh handles after zoom
    
    def zoomOut(self):
        zoom_factor = 0.8
        self.scale(zoom_factor, zoom_factor)
        self.currentZoom *= zoom_factor
        self.refreshTransformHandles()  # Refresh handles after zoom
    
    def resetZoom(self):
        self.resetTransform()
        self.currentZoom = 1.0
        self.refreshTransformHandles()  # Refresh handles after zoom

    def fitToWindow(self):
        if self.scene.sceneRect().isValid():
            # Get the current transform before fitting
            old_transform = self.transform()
            
            # Fit to view
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
            # Calculate the new zoom level based on the transform change
            new_transform = self.transform()
            self.currentZoom = new_transform.m11()
            self.refreshTransformHandles()  # Refresh handles after zoom
    
    def getSelectedLayersBounds(self) -> QRectF:
        """Get the bounding rectangle of all selected layers"""
        if not any(layer.selected for layer in self.layers):
            return QRectF()
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for layer in self.layers:
            if layer.selected and layer.visible:
                x = layer.position['x']
                y = layer.position['y']
                w = layer.pixmap.width()
                h = layer.pixmap.height()
                
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x + w)
                max_y = max(max_y, y + h)
        
        if min_x == float('inf'):
            return QRectF()
        
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def createTransformHandles(self, bounds: QRectF):
        """Create transform handles around the given bounds"""
        if bounds.isEmpty():
            return
        
        # Get the current view scale to make handles constant size
        handle_scale = 1.0 / self.currentZoom  # Inverse scale to counteract zoom
        
        # Corner handles
        corner_positions = [
            ('top_left', bounds.topLeft()),
            ('top_right', bounds.topRight()),
            ('bottom_left', bounds.bottomLeft()),
            ('bottom_right', bounds.bottomRight())
        ]
        
        # Edge handles
        edge_positions = [
            ('top', QPointF(bounds.center().x(), bounds.top())),
            ('bottom', QPointF(bounds.center().x(), bounds.bottom())),
            ('left', QPointF(bounds.left(), bounds.center().y())),
            ('right', QPointF(bounds.right(), bounds.center().y()))
        ]
        
        # Create corner handles
        for handle_type, pos in corner_positions:
            handle = TransformHandle('corner', None)
            handle.setPos(pos)
            handle.setScale(handle_scale)  # Apply inverse scale
            handle.setData(1, handle_type)  # Store handle position type
            self.scene.addItem(handle)
        
        # Create edge handles
        for handle_type, pos in edge_positions:
            handle = TransformHandle('edge', None)
            handle.setPos(pos)
            handle.setScale(handle_scale)  # Apply inverse scale
            handle.setData(1, handle_type)  # Store handle position type
            # Set appropriate cursor for edge handles
            if handle_type in ['top', 'bottom']:
                handle.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                handle.setCursor(Qt.CursorShape.SizeHorCursor)
            self.scene.addItem(handle)
    
    def refreshTransformHandles(self):
        """Refresh transform handles with current zoom level"""
        # Only refresh if there are selected layers
        if any(layer.selected for layer in self.layers):
            # Remove existing transform handles
            items_to_remove = []
            for item in self.scene.items():
                if isinstance(item, TransformHandle):
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                self.scene.removeItem(item)
            
            # Recreate handles with current zoom
            bounds = self.getSelectedLayersBounds()
            if not bounds.isEmpty():
                self.createTransformHandles(bounds)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert mouse position to scene coordinates
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # Check if we clicked on a transform handle
            item = self.scene.itemAt(scene_pos, self.transform())
            if item and isinstance(item, TransformHandle):
                self.isTransforming = True
                self.transformHandle = item
                self.transformHandleType = item.data(1)  # Store handle type to avoid accessing deleted object
                self.transformStartPosition = scene_pos
                
                # Store original scales and positions of selected layers
                self.selectedLayersStartScales = {}
                self.selectedLayersStartPositions = {}
                for layer in self.layers:
                    if layer.selected:
                        scale_x, scale_y = layer.getScale()
                        self.selectedLayersStartScales[layer] = {'x': scale_x, 'y': scale_y}
                        self.selectedLayersStartPositions[layer] = {
                            'x': layer.position['x'],
                            'y': layer.position['y']
                        }
                
                # Calculate bounding rect of selected layers
                self.transformBounds = self.getSelectedLayersBounds()
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
                return
            
            # Check if Ctrl is pressed
            ctrl_pressed = event.modifiers() == Qt.KeyboardModifier.ControlModifier
            
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
        if self.isTransforming and event.buttons() & Qt.MouseButton.LeftButton:
            # Calculate transform based on handle type
            current_pos = self.mapToScene(event.position().toPoint())
            handle_type = self.transformHandleType  # Use stored handle type instead of accessing deleted object
            
            # Calculate scale factors based on handle position
            bounds = self.transformBounds
            if bounds.isEmpty():
                return
            
            # Calculate relative position within bounds
            rel_start_x = (self.transformStartPosition.x() - bounds.left()) / bounds.width()
            rel_start_y = (self.transformStartPosition.y() - bounds.top()) / bounds.height()
            rel_current_x = (current_pos.x() - bounds.left()) / bounds.width()
            rel_current_y = (current_pos.y() - bounds.top()) / bounds.height()
            
            scale_x = 1.0
            scale_y = 1.0
            
            # Calculate scale factors based on handle type
            if handle_type in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                # Corner handles - proportional scaling
                if handle_type == 'top_left':
                    scale_x = 1.0 + (rel_start_x - rel_current_x)
                    scale_y = 1.0 + (rel_start_y - rel_current_y)
                elif handle_type == 'top_right':
                    scale_x = 1.0 + (rel_current_x - rel_start_x)
                    scale_y = 1.0 + (rel_start_y - rel_current_y)
                elif handle_type == 'bottom_left':
                    scale_x = 1.0 + (rel_start_x - rel_current_x)
                    scale_y = 1.0 + (rel_current_y - rel_start_y)
                elif handle_type == 'bottom_right':
                    scale_x = 1.0 + (rel_current_x - rel_start_x)
                    scale_y = 1.0 + (rel_current_y - rel_start_y)
            else:
                # Edge handles - single direction scaling
                if handle_type == 'top':
                    scale_y = 1.0 + (rel_start_y - rel_current_y)
                elif handle_type == 'bottom':
                    scale_y = 1.0 + (rel_current_y - rel_start_y)
                elif handle_type == 'left':
                    scale_x = 1.0 + (rel_start_x - rel_current_x)
                elif handle_type == 'right':
                    scale_x = 1.0 + (rel_current_x - rel_start_x)
            
            # Apply minimum scale to prevent negative or zero scaling
            scale_x = max(0.1, scale_x)
            scale_y = max(0.1, scale_y)
            
            # Apply scaling to all selected layers
            for layer in self.layers:
                if layer.selected:
                    original_scale = self.selectedLayersStartScales[layer]
                    new_scale_x = original_scale['x'] * scale_x
                    new_scale_y = original_scale['y'] * scale_y
                    layer.setScale(new_scale_x, new_scale_y)
                    
                    # Adjust position based on scaling anchor point
                    original_pos = self.selectedLayersStartPositions[layer]
                    anchor_x = bounds.left() + bounds.width() * rel_start_x
                    anchor_y = bounds.top() + bounds.height() * rel_start_y
                    
                    # Calculate new position relative to anchor
                    offset_x = original_pos['x'] - anchor_x
                    offset_y = original_pos['y'] - anchor_y
                    
                    new_x = anchor_x + offset_x * scale_x
                    new_y = anchor_y + offset_y * scale_y
                    
                    layer.setPosition(new_x, new_y)
            
            # Re-render the preview to show the updated transforms
            self.render(self.layers)
            
        elif self.isDragging and event.buttons() & Qt.MouseButton.LeftButton:
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
        if event.button() == Qt.MouseButton.LeftButton:
            if self.isTransforming:
                self.isTransforming = False
                self.transformHandle = None
                self.transformHandleType = ""  # Clear stored handle type
                self.selectedLayersStartScales.clear()
                self.selectedLayersStartPositions.clear()
                # Re-enable rubber band drag
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                # Emit signal to notify that layers have been transformed
                self.layerTransformed.emit()
            elif self.isDragging:
                self.isDragging = False
                self.selectedLayersStartPositions.clear()
                # Re-enable rubber band drag
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                # Emit signal to notify that layers have been moved
                self.layerTransformed.emit()
        
        super().mouseReleaseEvent(event)
    
    def render(self, layers: list[Layer]):
        # Store layers reference for click detection
        self.layers = layers
        self.scene.clear()

        # Calculate bounding rect for all layers
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')   
        
        # Track if any layers are selected
        has_selected_layers = False

        for layer in layers:
            if layer.visible:
                item = QGraphicsPixmapItem(layer.pixmap)
                item.setPos(layer.position['x'], layer.position['y'])
                item.setOpacity(layer.opacity)
                item.setData(0, "layer")
                self.scene.addItem(item)

                x = layer.position['x']
                y = layer.position['y']
                w = layer.pixmap.width()
                h = layer.pixmap.height()

                if layer.selected:
                    has_selected_layers = True
                    # Draw a selection rectangle around the layer
                    selection_rect = QGraphicsRectItem(x, y, w, h)
                    selection_rect.setPen(QPen(Qt.GlobalColor.blue, 2))
                    selection_rect.setBrush(QBrush(Qt.GlobalColor.transparent))
                    selection_rect.setData(0, "ui_element")
                    self.scene.addItem(selection_rect)
                
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x + w)
                max_y = max(max_y, y + h)
        
        # Add transform handles if there are selected layers
        if has_selected_layers:
            bounds = self.getSelectedLayersBounds()
            if not bounds.isEmpty():
                self.createTransformHandles(bounds)
        
        if min_x != float('inf'):
            self.scene.setSceneRect(min_x, min_y, max_x - min_x, max_y - min_y)