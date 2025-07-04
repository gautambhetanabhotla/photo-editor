from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QPixmap, QPainter, QPainter
from PySide6.QtCore import Qt

from preview import PreviewWindow
from layers import Layer, LayersWindow

class Composition():
    def __init__(self):
        self.layers = []
        self.selectedLayers = []  # Changed to list for multiple selection
        self.previewWindow = PreviewWindow()
        self.layersWindow = LayersWindow()
        
        # Connect layer selection signal
        self.previewWindow.layerClicked.connect(self.selectLayer)
        
        # Connect layer moved signal
        self.previewWindow.layerMoved.connect(self.update)

    def selectLayer(self, layer: Layer, ctrl_pressed: bool):
        """Select a layer, with Ctrl+click for multiple selection"""
        if ctrl_pressed:
            # Ctrl+click: toggle selection of the clicked layer
            if layer.selected:
                # Deselect if already selected
                layer.setSelected(False)
                if layer in self.selectedLayers:
                    self.selectedLayers.remove(layer)
            else:
                # Add to selection
                layer.setSelected(True)
                if layer not in self.selectedLayers:
                    self.selectedLayers.append(layer)
        else:
            # Normal click: select only this layer
            # Deselect all layers first
            for l in self.layers:
                l.setSelected(False)
            self.selectedLayers.clear()
            
            # Select the clicked layer
            if layer is not None:
                layer.setSelected(True)
                self.selectedLayers.append(layer)
        
        self.update()

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
                layer.selectionChanged.connect(self.update)
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