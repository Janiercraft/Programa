import os
import sys
import json
import tempfile
import shutil
import threading
import requests
import subprocess
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# URL pública de tu version.json
VERSION_JSON_URL = "https://raw.githubusercontent.com/Janiercraft/Programa/refs/heads/main/version.json"

# Rutas y nombres
CURRENT_EXE = sys.executable
EXE_DIR     = os.path.dirname(CURRENT_EXE)
OLD_EXE     = CURRENT_EXE + ".old"
LOGIN_SCRIPT = os.path.join(EXE_DIR, "login.py")  # ajusta si es distinto

def show_popup(title, message, auto_dismiss=True, duration=2):
    p = Popup(
        title=title,
        content=Label(text=message),
        size_hint=(0.6, 0.3),
        auto_dismiss=auto_dismiss
    )
    p.open()
    if auto_dismiss:
        Clock.schedule_once(lambda dt: p.dismiss(), duration)
    return p

def ensure_writable(path):
    return os.access(path, os.W_OK)

def automatic_rollback():
    if os.path.exists(OLD_EXE):
        try:
            shutil.copy(OLD_EXE, CURRENT_EXE)
            os.remove(OLD_EXE)
            show_popup("Rollback", "Error actualización. Volviendo a versión anterior.", duration=3)
            Clock.schedule_once(lambda dt: sys.exit(), 3)
        except:
            sys.exit()

def get_local_version():
    here = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    with open(os.path.join(here, "version.json"), "r") as f:
        return json.load(f)["version"]

def get_remote_data():
    r = requests.get(VERSION_JSON_URL, timeout=5)
    r.raise_for_status()
    return r.json()  # debe tener "version" y "url"

def is_newer(local, remote):
    lv = list(map(int, local.split(".")))
    rv = list(map(int, remote.split(".")))
    return rv > lv

def download_with_progress(url, on_complete, on_error, progress_bar):
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        fd, tmp_path = tempfile.mkstemp(suffix=".exe")
        os.close(fd)

        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                pct = downloaded / (total or 1)
                Clock.schedule_once(lambda dt, p=pct: setattr(progress_bar, "value", p), 0)

        Clock.schedule_once(lambda dt: on_complete(tmp_path), 0)

    except Exception as e:
        Clock.schedule_once(lambda dt: on_error(str(e)), 0)

def show_downloader_popup(download_url, apply_update_fn):
    layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
    lbl    = Label(text="Descargando actualización… 0%")
    pb     = ProgressBar(max=1.0, value=0.0)
    layout.add_widget(lbl)
    layout.add_widget(pb)

    popup = Popup(title="Actualizador", content=layout,
                  size_hint=(0.7, 0.3), auto_dismiss=False)
    popup.open()

    # Actualiza el texto del label cada 0.1s
    def update_label(dt):
        lbl.text = f"Descargando actualización… {int(pb.value*100)}%"
    popup._ev = Clock.schedule_interval(update_label, 0.1)

    def on_complete(tmp_path):
        Clock.unschedule(popup._ev)
        print(f"[DEBUG] Nuevo exe descargado en: {tmp_path}")
        popup.content.clear_widgets()
        popup.content.add_widget(Label(text=f"Descargado en:\n{tmp_path}"))
        Clock.schedule_once(lambda dt: (popup.dismiss(), apply_update_fn(tmp_path)), 2)


    def on_error(err):
        Clock.unschedule(popup._ev)
        popup.dismiss()
        show_popup("Error updater", err, duration=3)
        schedule_launch_login()

    threading.Thread(
        target=download_with_progress,
        args=(download_url, on_complete, on_error, pb),
        daemon=True
    ).start()

def apply_update(new_exe_path):
    if not ensure_writable(CURRENT_EXE) or not ensure_writable(EXE_DIR):
        show_popup("Error permisos",
                   "No se puede escribir aquí.\nEjecuta como admin o instala en carpeta de usuario.",
                   duration=4)
        return schedule_launch_login()

    if os.path.exists(OLD_EXE):
        os.remove(OLD_EXE)

    os.rename(CURRENT_EXE, OLD_EXE)
    shutil.copy(new_exe_path, CURRENT_EXE)
    os.chmod(CURRENT_EXE, 0o755)

    show_popup("Actualizado", "Reiniciando app...", duration=1)
    Clock.schedule_once(lambda dt: subprocess.Popen([CURRENT_EXE]), 1)
    Clock.schedule_once(lambda dt: sys.exit(), 1)

def schedule_launch_login():
    """Espera 2s y lanza login.py en un nuevo proceso"""
    def _launch(dt):
        if os.path.isfile(LOGIN_SCRIPT):
            subprocess.Popen([sys.executable, LOGIN_SCRIPT])
        sys.exit()
    Clock.schedule_once(_launch, 2)

def check_for_updates():
    # 1) rollback si queda .old
    automatic_rollback()

    # 2) popup buscando
    popup = show_popup("Actualizador", "Buscando actualizaciones…", auto_dismiss=False)

    def _do_check(dt):
        try:
            local_ver = get_local_version()
            data      = get_remote_data()
            remote_ver= data["version"]

            if is_newer(local_ver, remote_ver):
                popup.title   = "Actualizador"
                popup.content.text = f"Nueva versión v{remote_ver}\nPreparando descarga…"
                show_downloader_popup(data["url"], apply_update)
            else:
                popup.dismiss()
                show_popup("Actualizador", f"Ya estás en v{local_ver}")
                schedule_launch_login()

        except Exception as e:
            popup.dismiss()
            show_popup("Error updater", str(e), duration=3)
            schedule_launch_login()

    Clock.schedule_once(_do_check, 0.5)
