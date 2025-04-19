import numpy as np
from skimage.color import rgb2lab, lab2rgb

class ColorConverter:


    @staticmethod
    def hex_to_rgb(hex_color: str):
        """Konwertuje HEX na krotkę RGB (0-255)."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError("HEX musi być w formacie 6-cyfrowym (np. 'FFAABB')")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb: tuple):
        """Konwertuje krotkę RGB (0-255) na format HEX."""
        return "#{:02X}{:02X}{:02X}".format(*rgb)

    @staticmethod
    def hex_to_lab(hex_color: str):
        """Konwertuje HEX na LAB używając rgb2lab z skimage."""
        rgb = ColorConverter.hex_to_rgb(hex_color)
        rgb_scaled = np.array([[[c / 255.0 for c in rgb]]])
        lab = rgb2lab(rgb_scaled)
        return lab[0, 0, :]

    @staticmethod
    def lab_normalize(lab: tuple):
        """Normalizuje LAB do zakresu [0,1]."""
        L, a, b = lab
        L_norm = L / 100
        a_norm = (a + 128) / 255
        b_norm = (b + 128) / 255
        return (L_norm, a_norm, b_norm)

    @staticmethod
    def lab_denormalize(lab_norm: tuple):
        """Przywraca oryginalne zakresy LAB z wartości [0,1]."""
        L_norm, a_norm, b_norm = lab_norm
        L = L_norm * 100
        a = a_norm * 255 - 128
        b = b_norm * 255 - 128
        return (L, a, b)

    @staticmethod
    def lab_to_hex(L, a=None, b=None):
        """
            Konwertuje LAB na HEX poprzez przejście LAB -> RGB.
            Funkcja akceptuje:
            - trzy oddzielne argumenty (L, a, b), które mogą być typu float lub torch.Tensor,
            lub
            - pojedynczy argument iterowalny (np. krotkę, listę lub numpy array) zawierający trzy wartości.
        """
        # Jeżeli podany jest tylko jeden argument, oczekujemy, że jest to iterowalny obiekt zawierający trzy elementy.
        if a is None and b is None:
            try:
                L, a, b = L  # Próbujemy rozpakować pojedynczy iterowalny obiekt
            except TypeError:
                raise ValueError("Jeżeli przekazujesz jeden argument, musi to być iterowalny obiekt z trzema elementami")

        # Konwersja tensorów na float, jeśli konieczne
        if hasattr(L, "item"):
            L = L.item()
        if hasattr(a, "item"):
            a = a.item()
        if hasattr(b, "item"):
            b = b.item()

        # Przygotowanie tablicy LAB do konwersji
        lab = np.array([[[L, a, b]]])
        rgb = lab2rgb(lab)[0, 0, :]
        rgb_int = tuple(int(round(c * 255)) for c in rgb)
        return ColorConverter.rgb_to_hex(rgb_int)

    @staticmethod
    def rgb_to_lab(rgb: tuple):
        """Konwertuje RGB (0-255) na LAB używając rgb2lab z skimage."""
        rgb_scaled = np.array([[[c / 255.0 for c in rgb]]])
        lab = rgb2lab(rgb_scaled)
        return lab[0, 0, :]

    @staticmethod
    def lab_to_rgb(lab: tuple):
        """Konwertuje LAB na RGB (0-255) używając lab2rgb z skimage."""
        lab = np.array([[[lab[0], lab[1], lab[2]]]])
        rgb = lab2rgb(lab)[0, 0, :]
        return tuple(int(round(c * 255)) for c in rgb)