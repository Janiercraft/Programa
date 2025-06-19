import platform
from Clases_y_Funciones.Clases.gestion_recursos import Recursos

try:
    import winreg
except ImportError:
    winreg = None


def _es_modo_oscuro_windows() -> bool:
    """
    Lee la clave de registro en Windows para ver si el sistema
    está en modo oscuro (AppsUseLightTheme = 0). Si no es Windows
    o falla la lectura, devuelve False (modo claro).
    """
    if winreg is None:
        return False

    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as clave:
            valor, _ = winreg.QueryValueEx(clave, "AppsUseLightTheme")
            return (valor == 0)  # 0 = oscuro, 1 = claro
    except Exception:
        return False


def esta_en_modo_oscuro() -> bool:
    """
    Devuelve True si el sistema está en modo oscuro.
    Actualmente solo detecta modo oscuro en Windows. Para otros OS,
    siempre devuelve False (modo claro).
    """
    if platform.system() == "Windows":
        return _es_modo_oscuro_windows()
    return False


def obtener_ruta_fondo() -> str:
    """
    Devuelve la ruta completa al archivo de imagen de fondo,
    según el modo del sistema:
      - 'negro.jpg' si hay modo oscuro en Windows
      - 'blanco.jpg' en cualquier otro caso
    Usa Recursos.ruta() para regresar la ruta absoluta.
    """
    nombre = "negro.jpg" if esta_en_modo_oscuro() else "blanco.jpg"
    return Recursos.ruta(nombre)


def obtener_color_texto() -> tuple:
    """
    Devuelve una tupla RGBA con el color del texto que debe usarse
    sobre el fondo elegido. Si el sistema va en oscuro, devolvemos texto
    claro (1,1,1,1). Si el sistema va en claro, texto oscuro (0,0,0,1).
    """
    if esta_en_modo_oscuro():
        return (1, 1, 1, 1)   # blanco
    else:
        return (0, 0, 0, 1)   # negro