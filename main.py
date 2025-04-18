import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QMenuBar
from PySide6.QtGui import QPixmap, QPainter, QImage, QPaintEngine, QPainter, QGuiApplication
from PySide6.QtCore import Qt, QSize
from PIL import Image
from io import BytesIO

class Layer:
    def __init__(self, qimage: QImage):
        self.pixmap = QPixmap.fromImage(qimage)
        self.visible = True
        self.opacity = 1

class PreviewWindow(QWidget):
    def paintEvent(self, event):
        # Convention: Bottom layers are indexed first
        painter = QPainter(self)
        for layer in self.layerList:
            if layer.visible:
                painter.setOpacity(layer.opacity)
                painter.drawPixmap(0, 0, layer.pixmap)
        painter.end()
        # label = QLabel(self)
        # label.setPixmap(self.pixmap)

    def __init__(self, layerList: list[Layer] = []):
        super().__init__()
        self.layerList = layerList
        # self.renderLayers(0)
        label = QLabel(self)
        pixmap = QPixmap()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
    
    def __contains__(self, layer: Layer):
        return layer in self.layerList

    def __iter__(self):
        return iter(self.layerList)

    def importImage(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            for selectedFile in file_dialog.selectedFiles():
                qim = QImage(selectedFile)
                self.layerList.append(Layer(qim))
        self.update()

    def exportImage(self):
        if self.layerList:
            combined_pixmap = QPixmap(self.size())
            combined_pixmap.fill(Qt.GlobalColor.transparent)  # Fill with transparent color
            # Use QPainter to draw each layer onto the combined_pixmap
            painter = QPainter(combined_pixmap)
            for layer in self.layerList:
                if layer.visible:
                    painter.setOpacity(layer.opacity)
                    painter.drawPixmap(0, 0, layer.pixmap)
            painter.end()

            # Save the combined_pixmap to a file
            file_dialog = QFileDialog()
            save_path, _ = file_dialog.getSaveFileName(self, "Save Image File", "", "PNG Files (*.png)")
            if save_path:
                combined_pixmap.save(save_path, "PNG")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Editor")
        self.pixmap = QPixmap()
        self.layerList = []
        self.previewWindow = PreviewWindow(self.layerList)
        self.setCentralWidget(self.previewWindow)

        mainMenuBar = QMenuBar()
        fileMenu = mainMenuBar.addMenu("File")
        fileMenu.addAction("Import Image", self.previewWindow.importImage)
        fileMenu.addAction("Export Image", self.previewWindow.exportImage)
        self.setMenuBar(mainMenuBar)

        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        self.window_width = 800
        self.window_height = 600
        x_pos = int((screen_width - self.window_width) / 2)
        y_pos = int((screen_height - self.window_height) / 2)
        self.setGeometry(x_pos, y_pos, self.window_width, self.window_height)
    
    def resizeEvent(self, a0):
        return super().resizeEvent(a0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())