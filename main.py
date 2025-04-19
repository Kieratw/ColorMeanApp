import glob2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import dataclass
from typing import List, Dict, Optional
from Converter import ColorConverter


@dataclass
class PhotoVariant:
    file: str  # nazwa pliku tekstowego (np. osoba1.txt)
    photo: str  # nazwa zdjęcia (np. 000000010432.jpg)
    colors_hex: List[str]  # lista kolorów w formacie HEX (np. ["#FFAACC", "#123456", ...])
    colors_lab: List[List[float]]  # lista kolorów w formacie LAB, każdy jako [L, a, b]


def load_data(folder_path: str) -> Dict[str, Dict[str, List[PhotoVariant]]]:
    """
    Wczytuje wszystkie pliki .txt z danego folderu i zwraca słownik wariantów kolorów,
    pogrupowany według nazw zdjęć i osób (wyciągniętych z nazw plików .txt).

    Struktura wyniku:
    {
        "photo_name": {
            "person_name": [PhotoVariant, ...],
            ...
        },
        ...
    }
    """
    variants_by_photo_and_person: Dict[str, Dict[str, List[PhotoVariant]]] = {}

    for file_path in glob2.glob(f"{folder_path}/*.txt"):
        file_name = file_path.split("/")[-1]  # np. osoba1.txt
        person_name = file_name.replace(".txt", "")  # wyodrębnienie nazwy osoby, np. osoba1
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                photo_name = parts[0]  # np. 000000010432.jpg
                hex_colors = [color.strip(",") for color in parts[1:]]  # usuwanie przecinków
                lab_colors = [ColorConverter.hex_to_lab(hex_color) for hex_color in hex_colors]
                variant = PhotoVariant(
                    file=file_name,
                    photo=photo_name,
                    colors_hex=hex_colors,
                    colors_lab=lab_colors
                )
                if photo_name not in variants_by_photo_and_person:
                    variants_by_photo_and_person[photo_name] = {}
                if person_name not in variants_by_photo_and_person[photo_name]:
                    variants_by_photo_and_person[photo_name][person_name] = []
                variants_by_photo_and_person[photo_name][person_name].append(variant)

    return variants_by_photo_and_person


def create_3d_plot(variants_dict: Dict[str, Dict[str, List[PhotoVariant]]],
                   photo_name: Optional[str] = None,
                   num_colors: Optional[int] = None):
    """
    Tworzy interaktywny wykres 3D w przestrzeni CIE L*a*b* dla wybranych wariantów.

    Argumenty:
        variants_dict: Słownik wariantów w formacie {photo: {person: [PhotoVariant, ...]}}
        photo_name: Opcjonalna nazwa zdjęcia do filtrowania (np. '000000010432.jpg')
        num_colors: Opcjonalna liczba kolorów do filtrowania (np. 1, 2, 3, 4, 5)
    """
    # Przygotowanie listy wariantów do wyświetlenia
    variants_to_plot = []
    if photo_name and photo_name in variants_dict:
        for person in variants_dict[photo_name]:
            for variant in variants_dict[photo_name][person]:
                if num_colors is None or len(variant.colors_hex) == num_colors:
                    variants_to_plot.append(variant)
    else:
        for photo in variants_dict:
            for person in variants_dict[photo]:
                for variant in variants_dict[photo][person]:
                    if num_colors is None or len(variant.colors_hex) == num_colors:
                        variants_to_plot.append(variant)

    if not variants_to_plot:
        print("Brak próbek spełniających kryteria (zdjęcie lub liczba kolorów).")
        return

    # Przygotowanie danych do wykresu
    L_vals = []
    a_vals = []
    b_vals = []
    colors = []
    labels = []
    for variant in variants_to_plot:
        for color_lab, color_hex in zip(variant.colors_lab, variant.colors_hex):
            L_vals.append(color_lab[0])
            a_vals.append(color_lab[1])
            b_vals.append(color_lab[2])
            colors.append(color_hex)
            labels.append(f"{variant.file}: {variant.photo}")

    # Tworzenie wykresu 3D
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    scatter = ax.scatter(L_vals, a_vals, b_vals, c=colors, marker='o', s=50)

    # Etykiety osi
    ax.set_xlabel('L*')
    ax.set_ylabel('a*')
    ax.set_zlabel('b*')
    title = f"Kolory w przestrzeni CIE L*a*b*"
    if photo_name:
        title += f"\nZdjęcie: {photo_name}"
    if num_colors is not None:
        title += f", Liczba kolorów: {num_colors}"
    ax.set_title(title)

    # Inicjalizacja etykiety
    annot = None

    # Funkcja obsługi kliknięcia
    def on_click(event):
        nonlocal annot
        if event.inaxes == ax:
            cont, ind = scatter.contains(event)
            if cont:
                idx = ind["ind"][0]
                x_val = L_vals[idx]
                y_val = a_vals[idx]
                z_val = b_vals[idx]
                label_text = labels[idx]
                if annot:
                    annot.remove()
                annot = ax.text(x_val, y_val, z_val, label_text,
                                fontsize=9, color='black', backgroundcolor='white')
                fig.canvas.draw_idle()

    # Podłączenie obsługi zdarzenia kliknięcia
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()


# Przykład użycia
if __name__ == "__main__":
    # Wczytaj dane
    data = load_data("C:\\Users\\wojci\\Desktop\\TextFolder")  # Zastąp odpowiednią ścieżką
    # Wykres dla zdjęcia 000000010432.jpg, tylko próbki z 1 kolorem
    create_3d_plot(data, photo_name="000000191450.jpg", num_colors=1)
    create_3d_plot(data, photo_name="000000191450.jpg", num_colors=2)
    create_3d_plot(data, photo_name="000000191450.jpg", num_colors=3)
    create_3d_plot(data, photo_name="000000191450.jpg", num_colors=4)
    create_3d_plot(data, photo_name="000000191450.jpg", num_colors=5)
    # Wykres dla zdjęcia 000000010432.jpg, tylko próbki z 3 kolorami
    #create_3d_plot(data, photo_name="000000010432.jpg", num_colors=5)
    # Wykres dla wszystkich zdjęć, tylko próbki z 2 kolorami
    #create_3d_plot(data, num_colors=2)
    # Wykres dla konkretnego zdjęcia, wszystkie próbki
    #create_3d_plot(data, photo_name="000000022423.jpg")
    # Wykres dla wszystkich danych
    #create_3d_plot(data)