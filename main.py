import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QMenuBar, QDockWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame
from PySide6.QtGui import QPixmap, QPainter, QImage, QPaintEngine, QPainter, QGuiApplication, QKeySequence, QShortcut, QIcon
from PySide6.QtCore import Qt, QSize, QEvent, QObject, Signal
from PIL import Image
from io import BytesIO
import os

class Layer(QObject):
    visibilityChanged = Signal()

    def __init__(self, imagepath: str):
        super().__init__()
        self.pixmap = QPixmap.fromImage(QImage(imagepath))
        self.visible = True
        self.opacity = 1
        self.position = {'x': 0, 'y': 0}
        self.name = os.path.basename(imagepath)
        print(self.name)
        print(imagepath)
        
    def toggleVisibility(self):
        self.visible = not self.visible
        self.visibilityChanged.emit()
        print(f"Layer {self.name} visibility toggled to {self.visible}")
    
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
        return widget

class PreviewWindow(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene: QGraphicsScene = QGraphicsScene()
        self.setScene(self.scene)
        
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
    
    def render(self, layers: list[Layer]):
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
                
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x + w)
                max_y = max(max_y, y + h)
        
        if min_x != float('inf'):
            self.scene.setSceneRect(min_x, min_y, max_x - min_x, max_y - min_y)

class Composition():
    def __init__(self):
        self.layers = []
        self.previewWindow = PreviewWindow()
        self.layersWindow = LayersWindow()

    def update(self):
        self.previewWindow.render(self.layers)
        self.layersWindow.update(self.layers)

    def importImage(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            for selectedFile in file_dialog.selectedFiles():
                layer = Layer(selectedFile)
                self.layers.append(layer)
                layer.visibilityChanged.connect(self.update)
        self.update()

    def exportImage(self):
        if self.layers:
            # Get the scene rect for export size
            scene_rect = self.previewWindow.scene.sceneRect()
            combined_pixmap = QPixmap(scene_rect.size().toSize())
            combined_pixmap.fill(Qt.GlobalColor.transparent)
            
            # Render the scene to the pixmap
            painter = QPainter(combined_pixmap)
            self.previewWindow.scene.render(painter)
            painter.end()

            # Save the combined_pixmap to a file
            file_dialog = QFileDialog()
            save_path, _ = file_dialog.getSaveFileName(self.previewWindow, "Save Image File", "", "PNG Files (*.png)")
            if save_path:
                combined_pixmap.save(save_path, "PNG")

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

class MainWindow(QMainWindow):

    def update(self):
        super().update()
        self.activeComposition.update()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Editor")
        self.activeComposition = Composition()
        self.compositions = [self.activeComposition]

        mainMenuBar = QMenuBar()
        fileMenu = mainMenuBar.addMenu("File")
        fileMenu.addAction("Import Image", self.activeComposition.importImage)
        fileMenu.addAction("Export Image", self.activeComposition.exportImage)
        self.setMenuBar(mainMenuBar)

        # Layers window
        self.layersDockWidget = QDockWidget()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layersDockWidget)
        self.layersDockWidget.setWindowTitle("Layers")

        self.setCentralWidget(self.activeComposition.previewWindow)
        self.layersDockWidget.setWidget(self.activeComposition.layersWindow)

        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        initial_window_width = 800
        initial_window_height = 600
        # Center the window
        x_pos = int((screen_width - initial_window_width) / 2)
        y_pos = int((screen_height - initial_window_height) / 2)
        self.setGeometry(x_pos, y_pos, initial_window_width, initial_window_height)

    def setActiveComposition(self, composition: Composition):
        self.activeComposition = composition
        self.setCentralWidget(self.activeComposition.previewWindow)
        self.layersDockWidget.setWidget(self.activeComposition.layersWindow)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())