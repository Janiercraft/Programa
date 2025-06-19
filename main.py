import os
import sys
import json
import shutil
import requests
import subprocess
from pathlib import Path
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from Clases_y_Funciones.Clases.gestion_recursos import Recursos, RecursosExternos
from Clases_y_Funciones.Funciones.basesql import init_local_db, init_local_tasas
from UX.Login import LoginApp

# URL raw de tu version.json en GitHub
REMOTE_VERSION_JSON = (
    "https://raw.githubusercontent.com/Janiercraft/Programa/refs/heads/master/version.json"
)

def leer_json_interno():
    """
    Lee el version.json que está en la raíz del bundle (sys._MEIPASS)
    o en la carpeta del proyecto junto a main.py si no está frozen.
    """
    if getattr(sys, "frozen", False):
        # Modo onefile: version.json está en la raíz de _MEIPASS
        path = Path(sys._MEIPASS) / "version.json"
    else:
        # Modo desarrollo: version.json junto a main.py
        path = Path(__file__).parent / "version.json"

    if not path.exists():
        raise FileNotFoundError(f"version.json no encontrado en {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def leer_json_remoto():
    resp = requests.get(REMOTE_VERSION_JSON, timeout=10)
    resp.raise_for_status()
    return resp.json()

def lanzar_updater():
    # Usamos RecursosExternos.ruta para localizar updater.exe en recursos externos
    updater_path = Path(RecursosExternos.ruta("updater.exe"))
    if updater_path.exists():
        subprocess.Popen([str(updater_path), "--update"], cwd=str(updater_path.parent))
    sys.exit(0)

def mostrar_popup_actualizacion(local_v, remote_v):
    content = BoxLayout(orientation="vertical", spacing=10, padding=10)
    msg = Label(
        text=(
            f"Hay una nueva versión disponible:\n\n"
            f"Actual: {local_v}\n"
            f"Nueva:  {remote_v}"
        ),
        halign="center"
    )
    btns = BoxLayout(size_hint_y=None, height="40dp", spacing=10)
    btn_si = Button(text="Sí, actualizar")
    btn_no = Button(text="No, gracias")
    btns.add_widget(btn_si)
    btns.add_widget(btn_no)

    content.add_widget(msg)
    content.add_widget(btns)

    popup = Popup(
        title="Actualización disponible",
        content=content,
        size_hint=(0.75, 0.5),
        auto_dismiss=False
    )

    btn_si.bind(on_release=lambda *a: (popup.dismiss(), lanzar_updater()))
    btn_no.bind(on_release=lambda *a: popup.dismiss())
    popup.open()

class MainApp(LoginApp):
    def on_start(self):
        if hasattr(super(), "on_start"):
            super().on_start()

        def _check(dt):
            try:
                local_info  = leer_json_interno()
                remote_info = leer_json_remoto()
                lv = local_info.get("version", "")
                rv = remote_info.get("version", "")
                if lv and rv and lv != rv:
                    mostrar_popup_actualizacion(lv, rv)
            except Exception as e:
                print(f"[WARN] Chequeo de versión falló: {e}")

        Clock.schedule_once(_check, 0)

def main():
    # 1) Inicializa Kivy y la carpeta externa de Recursos
    RecursosExternos.init_kivy()

    # 2) Extrae updater.exe de la carpeta Recursos interna a la carpeta externa
    # Interno: Resources bajo el bundle o bajo el repo
    if getattr(sys, "frozen", False):
        internal_res_dir = Path(sys._MEIPASS) / "Recursos"
    else:
        internal_res_dir = Recursos.RECURSOS_DIR

    internal_updater = internal_res_dir / "updater.exe"
    external_updater = Path(RecursosExternos.ruta("updater.exe"))
    external_updater.parent.mkdir(parents=True, exist_ok=True)

    if internal_updater.exists() and not external_updater.exists():
        try:
            shutil.copy2(str(internal_updater), str(external_updater))
            print(f"[INFO] updater.exe extraído a {external_updater}")
        except Exception as e:
            print(f"[WARN] No pude extraer updater.exe: {e}")

    # 3) Inicializa/migra las bases de datos locales
    DB_PATH = Recursos.ruta("productos.db")
    if not os.path.exists(DB_PATH):
        print("[INFO] Base de datos local no encontrada. Creando...")
    else:
        print("[INFO] Base de datos encontrada. Verificando esquema...")
    init_local_db()
    init_local_tasas()

    # 4) Arranca la app (LoginApp con popup de actualización)
    MainApp().run()

if __name__ == "__main__":
    main()
