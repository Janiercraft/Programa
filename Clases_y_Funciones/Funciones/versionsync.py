import sys
import json
import shutil
from pathlib import Path

class VersionSync:
    """
    Sincroniza un version.json empaquetado con uno externo,
    copiando sólo cuando cambie la versión.
    """
    def __init__(self,
                 nombre_archivo: str = "version.json",
                 dir_externo: Path = None):
        # Nombre del fichero (por defecto version.json)
        self.nombre = nombre_archivo

        # Carpeta externa: por parámetro, o junto al .exe/.py
        if dir_externo is not None:
            self.dir_externo = Path(dir_externo)
        else:
            if getattr(sys, "frozen", False):
                self.dir_externo = Path(sys.executable).parent / "Recursos"
            else:
                self.dir_externo = Path(__file__).parent.parent / "Recursos"

        # Asegura la carpeta externa
        self.dir_externo.mkdir(parents=True, exist_ok=True)

        # Paths concretos
        self.ruta_externa = self.dir_externo / self.nombre
        self.ruta_interna = self._ruta_interna()

    def _ruta_interna(self) -> Path:
        """
        Devuelve la ruta al version.json dentro del bundle
        (sys._MEIPASS) o al lado del .py en desarrollo.
        """
        if getattr(sys, "frozen", False):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent
        return base / self.nombre

    def _leer_version(self, ruta: Path) -> str:
        """
        Lee el campo "version" de un version.json;
        devuelve None si no existe o no tiene campo.
        """
        if not ruta.exists():
            return None
        try:
            with ruta.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("version")
        except Exception:
            return None

    def sync(self) -> bool:
        """
        Compara versión interna vs externa. Si difieren,
        copia la interna sobre la externa y devuelve True.
        Si son iguales (o la interna no existe), no copia y devuelve False.
        """
        ver_int = self._leer_version(self.ruta_interna)
        ver_ext = self._leer_version(self.ruta_externa)

        # Si no hay version interna, nada que hacer
        if ver_int is None:
            return False

        # Sólo copia si cambió o si el externo no existía
        if ver_ext != ver_int:
            shutil.copy2(self.ruta_interna, self.ruta_externa)
            return True

        return False
