from typing import Dict, List, Tuple
from sklearn.cluster import KMeans
from Converter import ColorConverter
from PhotoVariant import PhotoVariant
import numpy as np

class ColorClusterer:
    def __init__(self, variants_by_photo_and_person: Dict[str, Dict[str, List[PhotoVariant]]]):

        self.variants = variants_by_photo_and_person

    def cluster_colors(self) -> Dict[str, Dict[int, List[Tuple[List[float], str]]]]:


        result: Dict[str, Dict[int, List[Tuple[List[float], str]]]] = {}
        for photo, persons in self.variants.items():
            result[photo] = {}
            for k in range(1, 6):
                # Collect all LAB points from variants with exactly k colors
                lab_points: List[List[float]] = []
                for variants in persons.values():
                    for variant in variants:
                        if len(variant.colors_lab) == k:
                            lab_points.extend(variant.colors_lab)
                if len(lab_points) < k:
                    # Not enough points to form k clusters
                    continue
                lab_array = np.array(lab_points)
                # KMeans clustering
                kmeans = KMeans(n_clusters=k, n_init='auto', random_state=0)
                kmeans.fit(lab_array)
                centroids = kmeans.cluster_centers_
                labels = kmeans.labels_
                # Determine cluster order by first occurrence in data
                order: List[int] = []
                seen = set()
                for lbl in labels:
                    if lbl not in seen:
                        seen.add(lbl)
                        order.append(lbl)
                    if len(order) == k:
                        break
                # Build ordered centroids list
                clusters: List[Tuple[List[float], str]] = []
                for lbl in order:
                    centroid = centroids[lbl]
                    lab_val = [float(c) for c in centroid]
                    hex_val = ColorConverter.lab_to_hex(lab_val)
                    clusters.append((lab_val, hex_val))
                result[photo][k] = clusters
        return result

    def save_clusters(self, output_file: str) -> None:

        clusters = self.cluster_colors()
        with open(output_file, 'w', encoding='utf-8') as f:
            for photo in sorted(clusters.keys()):
                for k in sorted(clusters[photo].keys()):
                    hex_codes = [hex_val for _, hex_val in clusters[photo][k]]
                    line = f"{photo}  " + ", ".join(hex_codes)
                    f.write(line + "\n")