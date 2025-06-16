import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QMenuBar, QDockWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QPainter, QImage, QPaintEngine, QPainter, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QSize, QEvent
from PIL import Image
from io import BytesIO

class Layer:
    def __init__(self, imagepath: str):
        self.pixmap = QPixmap.fromImage(QImage(imagepath))
        self.visible = True
        self.opacity = 1
        self.position = {'x': 0, 'y': 0}

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
        self.layersWindow.update()

    def importImage(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            for selectedFile in file_dialog.selectedFiles():
                self.layers.append(Layer(selectedFile))
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layers")
        self.setMinimumSize(QSize(200, 400))
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add buttons for each layer
        for i in range(5):
            button = QPushButton(f"Layer {i + 1}")
            layout.addWidget(button)

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
    
    def resizeEvent(self, event):
        print(event.size())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())