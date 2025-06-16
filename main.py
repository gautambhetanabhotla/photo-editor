import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QMenuBar, QDockWidget
from PySide6.QtGui import QPixmap, QPainter, QImage, QPaintEngine, QPainter, QGuiApplication
from PySide6.QtCore import Qt, QSize
from PIL import Image
from io import BytesIO

class Layer:
    def __init__(self, qimage: QImage):
        self.pixmap = QPixmap.fromImage(qimage)
        self.visible = True
        self.opacity = 1
        self.position = {'x': 0, 'y': 0}

class PreviewWindow(QWidget):
    def paintEvent(self, event):
        # Convention: Bottom layers are indexed first
        painter = QPainter(self)
        for layer in self.layers:
            if layer.visible:
                painter.setOpacity(layer.opacity)
                painter.drawPixmap(0, 0, layer.pixmap)
        painter.end()
        # label = QLabel(self)
        # label.setPixmap(self.pixmap)

    def __init__(self, layers: list[Layer] = []):
        super().__init__()
        # self.renderLayers(0)
        self.layers = layers
        label = QLabel(self)
        pixmap = QPixmap()
        label.setPixmap(pixmap)
        label.setScaledContents(True)

class Composition():
    def __init__(self):
        self.layers = []
        self.previewWindow = PreviewWindow()
        self.layersWindow = LayersWindow()

    def update(self):
        # self.previewWindow.update()
        self.previewWindow.layers = self.layers
        self.previewWindow.repaint()
        self.layersWindow.update()

    def importImage(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            for selectedFile in file_dialog.selectedFiles():
                qim = QImage(selectedFile)
                self.layers.append(Layer(qim))
        self.update()

    def exportImage(self):
        if self.layers:
            combined_pixmap = QPixmap(self.previewWindow.size())
            combined_pixmap.fill(Qt.GlobalColor.transparent)  # Fill with transparent color
            # Use QPainter to draw each layer onto the combined_pixmap
            painter = QPainter(combined_pixmap)
            for layer in self.layers:
                if layer.visible:
                    painter.setOpacity(layer.opacity)
                    painter.drawPixmap(0, 0, layer.pixmap)
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
        self.setGeometry(100, 100, 200, 400)
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
        # self.pixmap = QPixmap()
        # self.layerList = []
        # self.previewWindow = PreviewWindow(self.layerList)
        # self.setCentralWidget(self.previewWindow)
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
        self.window_width = 800
        self.window_height = 600
        # Center the window
        x_pos = int((screen_width - self.window_width) / 2)
        y_pos = int((screen_height - self.window_height) / 2)
        self.setGeometry(x_pos, y_pos, self.window_width, self.window_height)

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