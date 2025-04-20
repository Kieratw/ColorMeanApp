import sys
from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.cluster import KMeans
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QFileDialog, QMessageBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PhotoVariant import load_data as load_photo_variants
from mpl_toolkits.mplot3d import Axes3D
from Converter import ColorConverter
from Cluster import ColorClusterer  # import our clustering class

# Disable rotation and panning on 3D axes
def _disable_rotation(self, event):
    return
Axes3D._on_press = _disable_rotation
Axes3D._on_release = _disable_rotation
Axes3D._on_move = _disable_rotation

class ColorPlotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Color Plot Viewer")
        self.resize(1000, 900)

        # Data
        self.variants_by_photo_and_person: Dict[str, Dict[str, List]] = {}
        self.current_labels: List[str] = []
        self.clusters: Dict[str, Dict[int, List[Tuple[List[float], str]]]] = {}
        self.clusterer: Optional[ColorClusterer] = None

        # Controls
        self.load_button = QPushButton("Load Folder...")
        self.photo_list = QListWidget()
        self.colors_combo = QComboBox()
        self.colors_combo.addItem("All")
        for i in range(1, 6):
            self.colors_combo.addItem(str(i))
        self.plot_button = QPushButton("Plot 3D Colors")
        self.save_button = QPushButton("Save Clusters...")
        self.recluster_button = QPushButton("Recluster Photo")

        # Matplotlib
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Layouts
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Photo:"))
        controls_layout.addWidget(self.photo_list)
        controls_layout.addWidget(QLabel("# Colors:"))
        controls_layout.addWidget(self.colors_combo)
        controls_layout.addWidget(self.plot_button)
        controls_layout.addWidget(self.save_button)
        controls_layout.addWidget(self.recluster_button)

        # Image preview
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setStyleSheet("border: 1px solid #ccc")
        controls_layout.addWidget(self.image_label)

        self.cluster_layout = QHBoxLayout()
        self.cluster_layout.setSpacing(10)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.load_button)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.toolbar)
        main_layout.addLayout(self.cluster_layout)
        main_layout.addWidget(self.canvas)
        self.setLayout(main_layout)

        # Connections
        self.load_button.clicked.connect(self.load_data)
        self.plot_button.clicked.connect(self.update_plot)
        self.save_button.clicked.connect(self.on_save_clusters)
        self.recluster_button.clicked.connect(self.on_recluster)
        self.photo_list.currentItemChanged.connect(self.show_selected_photo)
        self.canvas.mpl_connect('pick_event', self.on_pick)

    def load_data(self):
        data_dir = QFileDialog.getExistingDirectory(self, "Select Data Folder", "", QFileDialog.ShowDirsOnly)
        if not data_dir:
            return
        photo_dir = QFileDialog.getExistingDirectory(self, "Select Photo Folder", "", QFileDialog.ShowDirsOnly)
        if not photo_dir:
            return

        self.data_folder = data_dir
        self.photo_folder = photo_dir
        self.variants_by_photo_and_person = load_photo_variants(self.data_folder)

        self.photo_list.clear()
        for photo in sorted(self.variants_by_photo_and_person.keys()):
            self.photo_list.addItem(photo)

        self.clusterer = ColorClusterer(self.variants_by_photo_and_person)
        self.clusters = self.clusterer.cluster_colors()

    def update_plot(self):
        # Clear previous cluster squares
        while self.cluster_layout.count():
            item = self.cluster_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()

        # Setup axes
        self.figure.clf()
        ax = self.figure.add_subplot(111, projection='3d')
        ax.set_xlim(0, 100)
        ax.set_ylim(-128, 127)
        ax.set_zlim(-128, 127)
        ax.set_xlabel('L*')
        ax.set_ylabel('a*')
        ax.set_zlabel('b*')

        photo_item = self.photo_list.currentItem()
        photo_name = photo_item.text() if photo_item else None
        k_text = self.colors_combo.currentText()
        num_colors = int(k_text) if k_text != "All" else None

        # Plot sRGB gamut
        gamut_L, gamut_a, gamut_b, gamut_colors = [], [], [], []
        N = 16
        for channel in range(3):
            for fixed in (0.0, 1.0):
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
        ax.scatter(gamut_L, gamut_a, gamut_b, c=gamut_colors, marker='.', s=10, alpha=0.6)

        # Plot measured variants
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
        if L_vals:
            ax.scatter(L_vals, a_vals, b_vals, c=colors, marker='o', s=80, picker=5, alpha=0.8)
        self.current_labels = labels

        # Plot centroids
        if photo_name and num_colors and self.clusters:
            photo_clusters = self.clusters.get(photo_name, {})
            centroids = photo_clusters.get(num_colors, [])
            for lab_val, hex_val in centroids:
                Lc, ac, bc = lab_val
                ax.scatter([Lc], [ac], [bc], c=[hex_val], marker='^', s=200, edgecolors='black')
                lbl = QLabel()
                lbl.setFixedSize(30, 30)
                lbl.setStyleSheet(f"background-color: {hex_val}; border: 1px solid #000;")
                self.cluster_layout.addWidget(lbl)

        self.canvas.draw()


    def on_recluster(self):
        photo_item = self.photo_list.currentItem()
        if not photo_item:
            QMessageBox.warning(self, "Brak wyboru", "Najpierw wybierz zdjęcie.")
            return
        photo_name = photo_item.text()
        k_text = self.colors_combo.currentText()
        if k_text == "All":
            QMessageBox.warning(self, "Brak wyboru", "Wybierz liczbę kolorów (k).")
            return
        k = int(k_text)

        # Gather LAB points for this photo and k
        lab_points = []
        for variants in self.variants_by_photo_and_person.get(photo_name, {}).values():
            for variant in variants:
                if len(variant.colors_lab) == k:
                    lab_points.extend(variant.colors_lab)
        if len(lab_points) < k:
            QMessageBox.warning(self, "Brak danych", f"Nie ma wystarczająco punktów do utworzenia {k} klastrów dla {photo_name}.")
            return

        lab_array = np.array(lab_points)
        # Use random_state=None for random init each recluster
        kmeans = KMeans(n_clusters=k, n_init='auto', random_state=None)
        kmeans.fit(lab_array)
        centroids_array = kmeans.cluster_centers_
        labels_idx = kmeans.labels_
        # Order clusters by first appearance
        order, seen = [], set()
        for lbl in labels_idx:
            if lbl not in seen:
                seen.add(lbl)
                order.append(lbl)
            if len(order) == k:
                break
        # Build new clusters list
        new_clusters: List[Tuple[List[float], str]] = []
        for lbl in order:
            centroid = centroids_array[lbl]
            lab_val = [float(c) for c in centroid]
            hex_val = ColorConverter.lab_to_hex(lab_val)
            new_clusters.append((lab_val, hex_val))

        self.clusters.setdefault(photo_name, {})[k] = new_clusters
        QMessageBox.information(self, "Przeliczono", f"Klustry dla {photo_name} (k={k}) przeliczone (random_state=None).")
        self.update_plot()

    def on_save_clusters(self):
        if not self.variants_by_photo_and_person:
            QMessageBox.warning(self, "Brak danych", "Najpierw wczytaj dane.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz klastry", "", "Pliki tekstowe (*.txt)")
        if not path:
            return
        try:
            self.clusterer.save_clusters(path)
            QMessageBox.information(self, "Zapisano", f"Zapisano do:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def on_pick(self, event):
        if hasattr(event, 'ind') and event.ind.size > 0:
            idx = event.ind[0]
            QMessageBox.information(self, "Point Info", f"Źródło: {self.current_labels[idx]}")

    def show_selected_photo(self, current, previous):
        if not current or not hasattr(self, "photo_folder"):
            self.image_label.clear()
            return
        base = current.text()
        photo_file = None

        path = os.path.join(self.photo_folder, base)
        if os.path.exists(path):
            photo_file = path


        if not photo_file:
            for fname in os.listdir(self.photo_folder):
                name, _ = os.path.splitext(fname)
                if name == base:
                    photo_file = os.path.join(self.photo_folder, fname)
                    break
        if not photo_file:
            self.image_label.clear()
            return
        pix = QPixmap(photo_file)
        pix = pix.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(pix)


def main():
    app = QApplication(sys.argv)
    window = ColorPlotApp()
    window.show()
    sys.exit(app.exec_())
