import glob2
from dataclasses import dataclass
from typing import List, Dict
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

    # Iteracja po wszystkich plikach .txt w folderze
    for file_path in glob2.glob(f"{folder_path}/*.txt"):
        file_name = file_path.split("/")[-1]  # np. osoba1.txt
        person_name = file_name.replace(".txt", "")  # wyodrębnienie nazwy osoby, np. osoba1
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue  # pominięcie pustych linii
                parts = line.split()
                if len(parts) < 2:  # pominięcie linii bez kolorów
                    continue
                photo_name = parts[0]  # np. 000000010432.jpg
                hex_colors = [color.strip(",") for color in parts[1:]]  # usuwanie przecinków
                # Konwersja każdego koloru HEX na LAB
                lab_colors = [ColorConverter.hex_to_lab(hex_color) for hex_color in hex_colors]
                variant = PhotoVariant(
                    file=file_name,
                    photo=photo_name,
                    colors_hex=hex_colors,
                    colors_lab=lab_colors
                )
                # Grupowanie wariantów według zdjęcia i osoby
                if photo_name not in variants_by_photo_and_person:
                    variants_by_photo_and_person[photo_name] = {}
                if person_name not in variants_by_photo_and_person[photo_name]:
                    variants_by_photo_and_person[photo_name][person_name] = []
                variants_by_photo_and_person[photo_name][person_name].append(variant)

    return variants_by_photo_and_person