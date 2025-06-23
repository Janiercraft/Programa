import os
import sys
import json
import shutil
import requests
import subprocess
from pathlib import Path
from kivy.metrics import sp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from Clases_y_Funciones.Clases.gestion_recursos import Recursos, RecursosExternos
from Clases_y_Funciones.Funciones.basesql import init_local_db, init_local_tasas
from UX.Login import LoginApp
from kivy.uix.anchorlayout import AnchorLayout

# —––––––––––––––––––––––––––––––––––––––––––––––––––—
# Configuración inicial de la ventana principal
# —––––––––––––––––––––––––––––––––––––––––––––––––––—
Window.title = "Calculadora R.Prestige"   # Título personalizado

# URL raw de tu version.json en GitHub
REMOTE_VERSION_JSON = (
    "https://raw.githubusercontent.com/Janiercraft/Programa/refs/heads/master/version.json"
)

def leer_json_interno():
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "version.json"
    else:
        path = Path(__file__).parent / "version.json"

    if not path.exists():
        raise FileNotFoundError(f"version.json no encontrado en {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def leer_json_remoto():
    resp = requests.get(REMOTE_VERSION_JSON, timeout=10)
    resp.raise_for_status()
    return resp.json()

def lanzar_updater():
    updater_path = Path(RecursosExternos.ruta("updater.exe"))
    if updater_path.exists():
        subprocess.Popen(
            [str(updater_path), "--update"],
            cwd=str(updater_path.parent)
        )
    sys.exit(0)

def mostrar_popup_actualizacion(local_v, remote_v):
    def get_responsive_font_size(base_sp=16):
        scale = Window.width / 500.0
        return sp(base_sp * scale)

    content = BoxLayout(
        orientation="vertical",
        spacing=10,
        padding=10,
    )

    # Usar anchor_x y anchor_y en lugar de anchor
    msg_container = AnchorLayout(
        size_hint=(1, 1),
        anchor_x='center',
        anchor_y='center',
    )

    msg = Label(
        text=(
            f"Hay una nueva versión disponible:\n"
            f"Actual: {local_v}\n"
            f"Nueva:  {remote_v}"
        ),
        halign="center",
        valign="middle",
        size_hint=(None, None),
        font_size=get_responsive_font_size(12),
    )
    def _update_size(label, _):
        label.size = label.texture_size
    msg.bind(texture_size=_update_size)

    msg_container.add_widget(msg)
    content.add_widget(msg_container)

    btns = BoxLayout(size_hint=(1, None), height="40dp", spacing=10)
    btn_si = Button(text="Sí, actualizar", size_hint=(0.5, 1),
                    font_size=get_responsive_font_size(12))
    btn_no = Button(text="No, gracias", size_hint=(0.5, 1),
                    font_size=get_responsive_font_size(12))
    btns.add_widget(btn_si)
    btns.add_widget(btn_no)
    content.add_widget(btns)

    popup = Popup(
        title="Actualización disponible",
        content=content,
        size_hint=(0.5, 0.86),
        auto_dismiss=False
    )
    popup.title_size = get_responsive_font_size(14)

    def _on_window_resize(*_):
        fs = get_responsive_font_size
        msg.font_size = fs(12)
        btn_si.font_size = fs(10)
        btn_no.font_size = fs(10)
        try:
            popup.title_size = fs(14)
        except AttributeError:
            popup._title_label.font_size = fs(14)
        msg.texture_update()

    Window.bind(on_resize=_on_window_resize)

    btn_si.bind(on_release=lambda *a: (popup.dismiss(), lanzar_updater()))
    btn_no.bind(on_release=lambda *a: popup.dismiss())
    popup.open()

class MainApp(LoginApp):
    # También se puede usar este atributo:
    title = "Calculadora R.Prestige"

    def build(self):
        # Si LoginApp define build(), lo llamamos para inicializar la UI
        root = super().build()
        Window.title = self.title
        return root

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