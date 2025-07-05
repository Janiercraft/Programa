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
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import App
from kivy.config import Config
Config.set('kivy', 'input_exclude', 'wm_pen')

from Clases_y_Funciones.Clases.gestion_recursos import Recursos, RecursosExternos
from Clases_y_Funciones.Funciones.basesql import init_local_db, init_local_tasas
from UX.Login import LoginApp

REMOTE_VERSION_JSON = "https://raw.githubusercontent.com/Janiercraft/Programa/refs/heads/master/version.json"

# Flags globales
update_pending = False
_updater_launched = False

def leer_json_interno():
    base = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent
    path = base / "version.json"
    return json.loads(path.read_text(encoding="utf-8"))

def leer_json_remoto():
    resp = requests.get(REMOTE_VERSION_JSON, timeout=10)
    resp.raise_for_status()
    return resp.json()

def lanzar_updater():
    global _updater_launched
    if _updater_launched:
        return
    _updater_launched = True

    exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    updater_path = exe_dir / "Recursos" / "updater.exe"
    if not updater_path.exists():
        return

    cmd = [str(updater_path), "--", "--update"]
    try:
        subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=str(updater_path.parent),
            shell=False,
        )
    except Exception:
        try:
            os.startfile(str(updater_path))
        except Exception:
            pass

class MainApp(LoginApp):
    title = "Calculadora R.Prestige"

    def build(self):
        Window.title = self.title
        return super().build()

    def on_start(self):
        super().on_start()
        Clock.schedule_once(lambda dt: self._check_update(), 0)

    def _check_update(self):
        try:
            lv = leer_json_interno().get("version", "")
            rv = leer_json_remoto().get("version", "")
            if lv and rv and lv != rv:
                self._mostrar_popup_actualizacion(lv, rv)
        except Exception:
            pass

    def _mostrar_popup_actualizacion(self, local_v, remote_v):
        def fs(base_sp=16):
            return sp(base_sp * (Window.width / 500.0))

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        msg = Label(
            text=(f"Hay una nueva versión disponible:\n"
                  f"Actual: {local_v}\n"
                  f"Nueva:  {remote_v}"),
            halign="center", valign="middle",
            size_hint=(None, None), font_size=fs(12),
        )
        msg.bind(texture_size=lambda l, _: setattr(l, 'size', l.texture_size))

        anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        anchor.add_widget(msg)
        content.add_widget(anchor)

        btns = BoxLayout(size_hint=(1, None), height="40dp", spacing=10)
        btn_si = Button(text="Sí, actualizar", font_size=fs(12))
        btn_no = Button(text="No, gracias",   font_size=fs(12))
        btns.add_widget(btn_si)
        btns.add_widget(btn_no)
        content.add_widget(btns)

        popup = Popup(
            title="Actualización disponible",
            content=content,
            size_hint=(0.5, 0.86),
            auto_dismiss=False,
        )

        Window.bind(on_resize=lambda *a: [
            setattr(msg,    'font_size', fs(12)),
            setattr(btn_si, 'font_size', fs(12)),
            setattr(btn_no, 'font_size', fs(12)),
            msg.texture_update()
        ])

        btn_si.bind(on_release=lambda *a, p=popup: (
            self._set_update_pending(),
            p.dismiss(),
            App.get_running_app().stop()
        ))
        btn_no.bind(on_release=lambda *a, p=popup: p.dismiss())

        popup.open()

    def _set_update_pending(self):
        global update_pending
        update_pending = True

    def on_stop(self):
        if update_pending:
            lanzar_updater()
        return super().on_stop()

def main():
    RecursosExternos.init_kivy()

    # Extraer updater.exe si es necesario
    exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    if getattr(sys, "frozen", False):
        internal_dir = Path(sys._MEIPASS) / "Recursos"
    else:
        internal_dir = Recursos.RECURSOS_DIR
    internal_updater = internal_dir / "updater.exe"

    out_dir = exe_dir / "Recursos"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "updater.exe"

    if internal_updater.exists() and not target.exists():
        shutil.copy2(str(internal_updater), str(target))

    init_local_db()
    init_local_tasas()

    MainApp().run()

if __name__ == "__main__":
    main()
