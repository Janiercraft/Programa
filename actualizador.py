import os
import sys
import json
import tempfile
import shutil
import requests
import subprocess
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup

# URL donde está tu version.json pública
VERSION_JSON_URL = "https://raw.githubusercontent.com/Janiercraft/Programa/refs/heads/main/version.json"

# Rutas y nombres
CURRENT_EXE = sys.executable
EXE_DIR = os.path.dirname(CURRENT_EXE)
EXE_NAME = os.path.basename(CURRENT_EXE)
OLD_EXE = CURRENT_EXE + ".old"


def show_popup(title, message, auto_dismiss=True, duration=2):
    popup = Popup(
        title=title,
        content=Label(text=message),
        size_hint=(0.6, 0.3),
        auto_dismiss=auto_dismiss
    )
    popup.open()
    if auto_dismiss:
        Clock.schedule_once(lambda dt: popup.dismiss(), duration)
    return popup


def ensure_writable(path):
    return os.access(path, os.W_OK)


def automatic_rollback():
    """Si existe OLD_EXE, restaura sin preguntar."""
    if os.path.exists(OLD_EXE):
        try:
            shutil.copy(OLD_EXE, CURRENT_EXE)
            os.remove(OLD_EXE)
            show_popup(
                "Error actualización",
                "Se produjo un error. Volviendo a la versión anterior.",
                duration=3
            )
            Clock.schedule_once(lambda dt: sys.exit(), 3)
        except Exception:
            sys.exit()


def get_local_version():
    here = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    vfile = os.path.join(here, "version.json")
    try:
        text = open(vfile, "r").read()
        print(f"[DEBUG] version.json local ({vfile}):\n{text}")
        data = json.loads(text)
        local_ver = data.get("version", "").strip()
        print(f"[DEBUG] Versión local parseada: {local_ver!r}")
        return local_ver
    except Exception as e:
        print(f"[DEBUG] Error leyendo version.json local: {e}")
        return "0.0.0"


def get_remote_data():
    try:
        r = requests.get(VERSION_JSON_URL, timeout=5)
        print(f"[DEBUG] GET {VERSION_JSON_URL} → {r.status_code}")
        print(f"[DEBUG] BODY remoto:\n{r.text}\n---")
        r.raise_for_status()
        data = r.json()
        # Aseguramos campos
        if "version" not in data or "url" not in data:
            raise ValueError("JSON remoto inválido, falta 'version' o 'url'")
        return {
            "version": data["version"].strip(),
            "url": data["url"].strip()
        }
    except Exception as e:
        print(f"[DEBUG] Error obteniendo datos remotos: {e}")
        return None


def is_newer(local, remote):
    try:
        lv = list(map(int, local.split(".")))
        rv = list(map(int, remote.split(".")))
        return rv > lv
    except Exception as e:
        print(f"[DEBUG] Error comparando versiones: {e}")
        return False


def download_new_exe(url):
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    fd, tmp_path = tempfile.mkstemp(suffix=".exe")
    os.close(fd)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(r.raw, f)

    print(f"[DEBUG] Nuevo ejecutable descargado en: {tmp_path}")
    show_popup("Descarga completada", f"Nuevo archivo descargado en:\n{tmp_path}", duration=4)
    return tmp_path


def apply_update(new_exe_path):
    if not ensure_writable(CURRENT_EXE) or not ensure_writable(EXE_DIR):
        show_popup(
            "Error permisos",
            "No se pueden escribir archivos aquí.\nEjecuta como admin o instala en tu carpeta de usuario.",
            duration=4
        )
        return

    # Rollback guard: eliminamos cualquier .old previo
    if os.path.exists(OLD_EXE):
        os.remove(OLD_EXE)

    # Renombrar exe actual y copiar el nuevo
    try:
        os.rename(CURRENT_EXE, OLD_EXE)
        print(f"[DEBUG] Ejecutable actual renombrado a: {OLD_EXE}")
    except Exception as e:
        print(f"[ERROR] No se pudo renombrar el actual a .old: {e}")
        show_popup("Error", f"No se pudo hacer backup del ejecutable:\n{e}", duration=4)
        return

    try:
        shutil.copy(new_exe_path, CURRENT_EXE)
        os.chmod(CURRENT_EXE, 0o755)
        print(f"[DEBUG] Nuevo ejecutable copiado a: {CURRENT_EXE}")
    except Exception as e:
        print(f"[ERROR] Falló al copiar el nuevo .exe: {e}")
        show_popup("Error", f"No se pudo aplicar actualización:\n{e}", duration=4)
        automatic_rollback()
        return

    show_popup("Actualizado", "Reiniciando app...", duration=2)
    subprocess.Popen([CURRENT_EXE])
    sys.exit()

def check_for_updates():
    # 1) Rollback automático si queda un .old
    automatic_rollback()

    # 2) Mostrar popup de búsqueda
    popup = show_popup("Actualizador", "Buscando actualizaciones...", auto_dismiss=False)

    def _do_check(dt):
        try:
            local_ver = get_local_version()
            data = get_remote_data()
            if not data:
                popup.dismiss()
                show_popup("Actualizador", "No se pudo obtener versión remota.", duration=3)
                return

            remote_ver = data["version"]
            print(f"[DEBUG] Versión remota parseada: {remote_ver!r}")

            # 3) Comparar versiones
            if is_newer(local_ver, remote_ver):
                print("[DEBUG] Se detectó versión nueva")
                popup.title = "Actualizador"
                popup.content.text = f"Nueva versión {remote_ver}\nDescargando..."
                new_exe = download_new_exe(data["url"])
                popup.dismiss()
                apply_update(new_exe)
            else:
                print("[DEBUG] No hay actualización (remote≤local)")
                popup.dismiss()
                show_popup("Actualizador", f"Ya estás en v{local_ver}", duration=2)
        except Exception as e:
            print(f"[DEBUG] Excepción en updater: {e}")
            popup.dismiss()
            show_popup("Error updater", str(e), duration=3)

    Clock.schedule_once(_do_check, 0.5)