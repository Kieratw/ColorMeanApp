import sys
from typing import Dict, List, Optional
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QFileDialog, QMessageBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PhotoVariant import load_data as load_photo_variants
from mpl_toolkits.mplot3d import Axes3D
from Converter import ColorConverter

# Disable only rotation and panning for 3D axes, but leave scroll zoom
def _disable_rotation(self, event):
    return
Axes3D._on_press = _disable_rotation
Axes3D._on_release = _disable_rotation
Axes3D._on_move = _disable_rotation

class ColorPlotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Color Plot Viewer")
        self.resize(1000, 800)

        # Data structure
        self.variants_by_photo_and_person: Dict[str, Dict[str, List]] = {}
        self.current_labels: List[str] = []

        # UI elements
        self.load_button = QPushButton("Load Folder...")
        self.photo_list = QListWidget()
        self.colors_combo = QComboBox()
        self.colors_combo.addItem("All")
        for i in range(1, 6):
            self.colors_combo.addItem(str(i))
        self.plot_button = QPushButton("Plot 3D Colors")

        # Matplotlib canvas and toolbar for zoom
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Layout setup
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Photo:"))
        controls_layout.addWidget(self.photo_list)
        controls_layout.addWidget(QLabel("# Colors:"))
        controls_layout.addWidget(self.colors_combo)
        controls_layout.addWidget(self.plot_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.load_button)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.canvas)
        self.setLayout(main_layout)

        # Connect signals
        self.load_button.clicked.connect(self.load_data)
        self.plot_button.clicked.connect(self.update_plot)
        self.canvas.mpl_connect('pick_event', self.on_pick)

    def load_data(self):
        """Load all .txt files in folder using PhotoVariant.load_data"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Data Folder", "", QFileDialog.ShowDirsOnly
        )
        if not folder_path:
            return
        self.variants_by_photo_and_person = load_photo_variants(folder_path)
        self.photo_list.clear()
        for photo in sorted(self.variants_by_photo_and_person.keys()):
            self.photo_list.addItem(photo)

    def update_plot(self):
        # Choose photo and color count
        photo_name = self.photo_list.currentItem().text() if self.photo_list.currentItem() else None
        combo_text = self.colors_combo.currentText()
        num_colors: Optional[int] = None
        if combo_text != "All":
            num_colors = int(combo_text)

        # Gather measured data
        L_vals, a_vals, b_vals, colors, labels = [], [], [], [], []
        data_dict = {photo_name: self.variants_by_photo_and_person.get(photo_name, {})} if photo_name else self.variants_by_photo_and_person
        for persons in data_dict.values():
            for variants in persons.values():
                for variant in variants:
                    if num_colors is None or len(variant.colors_hex) == num_colors:
                        for (L, a, b), hex_col in zip(variant.colors_lab, variant.colors_hex):
                            L_vals.append(L)
                            a_vals.append(a)
                            b_vals.append(b)
                            colors.append(hex_col)
                            labels.append(variant.file)

        if not L_vals:
            QMessageBox.information(self, "No Data", "No samples match the criteria.")
            return

        # Plot
        self.figure.clf()
        ax = self.figure.add_subplot(111, projection='3d')

        # Fixed axes limits
        ax.set_xlim(0, 100)
        ax.set_ylim(-128, 127)
        ax.set_zlim(-128, 127)
        ax.set_xlabel('L*')
        ax.set_ylabel('a*')
        ax.set_zlabel('b*')
        ax.set_title(
            f"Colors in CIE L*a*b*{f' — {photo_name}' if photo_name else ''}"
            f"{f', # colors = {num_colors}' if num_colors else ''}"
        )

        # sRGB gamut boundary surface
        gamut_L, gamut_a, gamut_b, gamut_colors = [], [], [], []
        N = 16
        for channel in range(3):
            for fixed in [0.0, 1.0]:
                u = np.linspace(0, 1, N)
                v = np.linspace(0, 1, N)
                for uu in u:
                    for vv in v:
                        rgb = [0.0, 0.0, 0.0]
                        rgb[channel] = fixed
                        rgb[(channel+1)%3] = uu
                        rgb[(channel+2)%3] = vv
                        Lg, ag, bg = ColorConverter.rgb_to_lab(tuple(rgb))
                        gamut_L.append(Lg)
                        gamut_a.append(ag)
                        gamut_b.append(bg)
                        gamut_colors.append(tuple(rgb))
        ax.scatter(
            gamut_L, gamut_a, gamut_b,
            c=gamut_colors, marker='.', s=10, alpha=0.6
        )

        # Measured points
        ax.scatter(
            L_vals, a_vals, b_vals,
            c=colors, marker='o', s=80, picker=5
        )

        self.current_labels = labels
        self.canvas.draw()

    def on_pick(self, event):
        if hasattr(event, 'ind') and event.ind.size > 0:
            idx = event.ind[0]
            QMessageBox.information(
                self, "Point Info", f"Source file: {self.current_labels[idx]}"
            )


def main():
    app = QApplication(sys.argv)
    window = ColorPlotApp()
    window.show()
    sys.exit(app.exec_())
