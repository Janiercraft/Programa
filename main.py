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
    "https://raw.githubusercontent.com/Janiercraft/Programa/"
    "main/version.json"
)

def leer_json_interno():
    base = getattr(sys, "_MEIPASS", Path(__file__).parent)
    path = os.path.join(base, "version.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def leer_json_remoto():
    resp = requests.get(REMOTE_VERSION_JSON, timeout=10)
    resp.raise_for_status()
    return resp.json()

def lanzar_updater():
    recursos = Path(RecursosExternos._get_dir())
    updater = recursos / "updater.exe"
    if updater.exists():
        subprocess.Popen([str(updater), "--update"], cwd=str(recursos))
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

    def on_si(instance):
        popup.dismiss()
        lanzar_updater()

    def on_no(instance):
        popup.dismiss()

    btn_si.bind(on_release=on_si)
    btn_no.bind(on_release=on_no)
    popup.open()

class MainApp(LoginApp):
    def on_start(self):
        if hasattr(super(), "on_start"):
            super().on_start()

        def _check(dt):
            try:
                local_info  = leer_json_interno()
                remote_info = leer_json_remoto()
                local_v  = local_info .get("version", "")
                remote_v = remote_info.get("version", "")
                if local_v and remote_v and local_v != remote_v:
                    mostrar_popup_actualizacion(local_v, remote_v)
            except Exception:
                pass

        Clock.schedule_once(_check, 0)

def main():
    # 1) Inicializa Kivy y RecursosExternos
    RecursosExternos.init_kivy()
    ext_dir = Path(RecursosExternos._get_dir())

    # 2) Extrae el updater.exe embebido la primera vez
    internal_base = getattr(sys, "_MEIPASS", Path(__file__).parent)
    internal_updater = Path(internal_base) / "updater.exe"
    external_updater = ext_dir / "updater.exe"
    if internal_updater.exists() and not external_updater.exists():
        shutil.copy2(str(internal_updater), str(external_updater))

    # 3) Inicializa o migra tus bases de datos locales
    DB_PATH = Recursos.ruta("productos.db")
    if not os.path.exists(DB_PATH):
        print("[INFO] Base de datos local no encontrada. Creando...")
    else:
        print("[INFO] Base de datos encontrada. Verificando esquema...")
    init_local_db()
    init_local_tasas()

    # 4) Arranca la app con chequeo de actualización
    MainApp().run()

if __name__ == "__main__":
    main()
