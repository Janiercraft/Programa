import sys
import json
import subprocess
from pathlib import Path

import requests

from kivy.app              import App
from kivy.metrics          import sp, dp
from kivy.clock            import Clock
from kivy.core.window      import Window
from kivy.uix.popup        import Popup
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label        import Label
from kivy.uix.button       import Button

from Clases_y_Funciones.Clases.gestion_recursos import Recursos, RecursosExternos

GITHUB_JSON_URL = "https://raw.githubusercontent.com/Janiercraft/Programa/refs/heads/master/version.json"


def _locate_local_version_file():
    base = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent
    return base / "version.json"


def _load_json(path: Path):
    data = json.loads(path.read_text(encoding='utf-8'))
    return data.get("version"), data.get("url")


def _load_local_version():
    p = _locate_local_version_file()
    if not p.exists():
        raise FileNotFoundError(f"version.json no encontrado en {p}")
    return _load_json(p)


def _load_remote_version():
    r = requests.get(GITHUB_JSON_URL, timeout=5)
    r.raise_for_status()
    data = r.json()
    return data.get("version"), data.get("url")


def _version_tuple(v: str):
    return tuple(int(x) for x in v.split("."))


class UpdatePopup(Popup):
    def __init__(self, loc_ver, loc_url, rem_ver, rem_url, **kwargs):
        # 1) Contenedor vertical
        content = BoxLayout(orientation="vertical", spacing=10, padding=20)

        # 2) Mensaje centrado, ocupa 80% en Y
        anchor = AnchorLayout(size_hint=(1, 0.8))
        self._lbl = Label(
            text=(
                f"¡Hay una nueva versión disponible!\n\n"
                f"Actual: {loc_ver}   Nueva: {rem_ver}"
            ),
            halign="center", valign="middle",
            size_hint=(None, None)
        )
        # Ajusta su size a la textura (una línea)
        self._lbl.bind(texture_size=lambda lbl, ts: setattr(lbl, 'size', ts))
        anchor.add_widget(self._lbl)
        content.add_widget(anchor)

        # 3) Botones en 20% restante
        btns = BoxLayout(size_hint=(1, 0.2), spacing=10)
        self._yes = Button(text="Sí, actualizar")
        self._no  = Button(text="No, gracias")
        btns.add_widget(self._yes)
        btns.add_widget(self._no)
        content.add_widget(btns)

        # 4) Popup con size_hint para ancho y altura dinámica
        super().__init__(
            title="Actualización disponible",
            content=content,
            size_hint=(0.6, 0.4),  # 60% ancho, 40% alto de Window
            auto_dismiss=False,
            **kwargs
        )

        # Guardamos la URL remota si la necesitas
        self.remote_url = rem_url

        # Bind botones
        self._yes.bind(on_release=self._on_accept)
        self._no .bind(on_release=lambda *a: self.dismiss())

        # Ajustes iniciales y al redimensionar
        self.bind(on_open=lambda *a: self._on_resize())
        Window.bind(on_resize=lambda *a: self._on_resize())

    def _on_resize(self, *args):
        # Reajusta el tamaño del popup a 40% de la ventana
        self.size = (Window.width * 0.6, Window.height * 0.4)

        # Escala fuentes según ancho del popup
        fs = lambda base: sp(base * (self.width / 500.0))
        self._lbl.font_size = fs(14)
        self._yes.font_size = fs(12)
        self._no.font_size  = fs(12)
        self._lbl.texture_update()

    def _on_accept(self, *args):
        """
        Lanza updater.exe y cierra la app.
        """
        path_str = (RecursosExternos.ruta("updater.exe")
                    if getattr(sys, 'frozen', False)
                    else Recursos.ruta("updater.exe"))
        updater_path = Path(path_str)
        print(f"[UPDATE] Lanzando updater: {updater_path}")
        if updater_path.exists():
            subprocess.Popen([str(updater_path)])
            App.get_running_app().stop()
        else:
            print(f"[UPDATE] ERROR: no existe {updater_path}")
        self.dismiss()


def show_update_popup():
    """
    Lee versiones local/remota, compara y muestra el popup
    solo si la remota es mayor.
    """
    try:
        loc_ver, loc_url = _load_local_version()
        print(f"[UPDATE] LOCAL  {loc_ver} ({loc_url})")
        rem_ver, rem_url = _load_remote_version()
        print(f"[UPDATE] REMOTA {rem_ver} ({rem_url})")
    except Exception as e:
        print(f"[UPDATE] Error cargando versiones: {e!r}")
        return

    if _version_tuple(rem_ver) > _version_tuple(loc_ver):
        print(f"[UPDATE] remota > local → mostrando popup")
        UpdatePopup(loc_ver, loc_url, rem_ver, rem_url).open()
    else:
        print(f"[UPDATE] ya estás en la versión {loc_ver} → no mostrar popup")