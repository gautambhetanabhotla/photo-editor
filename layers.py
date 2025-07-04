from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QPixmap, QImage, QIcon
from PySide6.QtCore import QSize, QObject, Signal, QPointF
import os

class Layer(QObject):
    visibilityChanged = Signal()
    selectionChanged = Signal()

    def __init__(self, imagepath: str):
        super().__init__()
        self.pixmap = QPixmap.fromImage(QImage(imagepath))
        self.visible = True
        self.selected = False
        self.image = QImage(imagepath)  # Store original image for pixel checking
        self.opacity = 1
        self.position = {'x': 0, 'y': 0}
        self.name = os.path.basename(imagepath)
        
    def toggleVisibility(self):
        self.visible = not self.visible
        self.visibilityChanged.emit()
        # print(f"Layer {self.name} visibility toggled to {self.visible}")
    
    def setSelected(self, selected: bool):
        if self.selected != selected:
            self.selected = selected
            self.selectionChanged.emit()
            # print(f"Layer {self.name} selection changed to {self.selected}")
    
    def containsPoint(self, point: QPointF) -> bool:
        """Check if the given point is within this layer's bounds and on a non-transparent pixel"""
        x, y = self.position['x'], self.position['y']
        w, h = self.image.width(), self.image.height()
        
        # First check if point is within bounds
        if not (x <= point.x() <= x + w and y <= point.y() <= y + h):
            return False
        
        # Calculate relative position within the image
        rel_x = int(point.x() - x)
        rel_y = int(point.y() - y)
        
        # Ensure coordinates are within image bounds (safety check)
        if rel_x < 0 or rel_x >= w or rel_y < 0 or rel_y >= h:
            return False
        
        # Get the pixel color at the clicked position
        pixel_color = self.image.pixelColor(rel_x, rel_y)
        
        # Check if the pixel is non-transparent (alpha > 0)
        return pixel_color.alpha() > 0
    
    def setPosition(self, x: float, y: float):
        """Set the position of the layer"""
        self.position['x'] = int(x)
        self.position['y'] = int(y)
    
    def widget(self):
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        label = QLabel(self.name)
        layout.addWidget(label)
        visibility_button = QPushButton()
        visibility_button.setIcon(QIcon("./assets/eye.png"))
        visibility_button.clicked.connect(self.toggleVisibility)
        layout.addStretch()
        layout.addWidget(visibility_button)
        
        # Update widget style based on selection
        if self.selected:
            widget.setStyleSheet("QWidget { background-color: #666666; border-radius: 3px; }")
        else:
            widget.setStyleSheet("")
        
        return widget

class LayersWindow(QWidget):

    class LayerWidget(QWidget):
        def __init__(self, layer: Layer):
            super().__init__()
            self.layer = layer
            layout = QHBoxLayout()
            self.setLayout(layout)
            self.label = QLabel(layer.name)
            layout.addWidget(self.label)
            layout.addStretch()
        
        def toggleVisibility(self):
            self.layer.visible = not self.layer.visible

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layers")
        self.setMinimumSize(QSize(200, 400))
        self.layout: QVBoxLayout = QVBoxLayout()
        self.setLayout(self.layout)

    def clearLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update(self, layers: list[Layer]):
        self.clearLayout()

        for idx, layer in enumerate(layers[::-1]):
            layer_widget = layer.widget()
            self.layout.addWidget(layer_widget)
            # Add divider after each widget except the last one
            if idx < len(layers) - 1:
                divider = QFrame()
                divider.setFrameShape(QFrame.Shape.HLine)
                divider.setFrameShadow(QFrame.Shadow.Sunken)
                divider.setMaximumHeight(1)
                self.layout.addWidget(divider)
        self.layout.addStretch()