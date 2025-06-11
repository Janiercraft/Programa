from pathlib import Path
from kivy.resources import resource_add_path

class Recursos:
    """
    Clase con métodos y atributos estáticos para obtener rutas absolutas
    y registrar la carpeta de recursos en Kivy.
    """
    # Directorio raíz del proyecto (dos niveles arriba de este carpeta)
    BASE_DIR = Path(__file__).parents[2]
    # Carpeta de recursos dentro del proyecto
    RECURSOS_DIR = BASE_DIR / 'Recursos'

    @classmethod
    def init_kivy(cls):
        """
        Registra la carpeta de recursos en Kivy para poder cargar imágenes,
        fuentes y otros assets solo con el nombre de archivo, y crea el
        directorio si no existe.
        """
        # Asegura que la carpeta de recursos exista
        cls.RECURSOS_DIR.mkdir(parents=True, exist_ok=True)
        resource_add_path(str(cls.RECURSOS_DIR))

    @classmethod
    def ruta(cls, nombre_archivo: str) -> str:
        """
        Devuelve la ruta absoluta de un recurso dado su nombre.
        No lanza errores si el archivo aún no existe; simplemente devuelve
        la ubicación donde debería estar.
        """
        # Asegura que la carpeta de recursos exista
        cls.RECURSOS_DIR.mkdir(parents=True, exist_ok=True)
        # Construye y devuelve la ruta completa (el archivo puede crearse luego)
        return str(cls.RECURSOS_DIR / nombre_archivo)

# Inicializar recursos al importar
Recursos.init_kivy()
