import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QDockWidget
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

from composition import Composition

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