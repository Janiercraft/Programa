# updater.py

import os
import sys
import json
import tempfile
import shutil
import requests
import subprocess

# URL pública donde tienes tu version.json de la release
VERSION_JSON_URL = "https://raw.githubusercontent.com/Janiercraft/Programa/refs/heads/main/version.json?token=GHSAT0AAAAAADFMEO5EWQ2VPFXZZRWJL6522CIYUYA"

# Nombre de tu ejecutable dentro de dist/
EXE_NAME = os.path.basename(sys.executable)

def get_local_version():
    """Lee version.json local para saber qué versión estoy ejecutando."""
    here = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    vfile = os.path.join(here, "version.json")
    try:
        with open(vfile, "r") as f:
            return json.load(f)["version"]
    except Exception:
        return "0.0.0"

def get_remote_data():
    """Descarga y parsea el version.json remoto."""
    r = requests.get(VERSION_JSON_URL, timeout=5)
    r.raise_for_status()
    return r.json()  # debe tener keys "version" y "url"

def is_newer(local, remote):
    """Compara dos strings 'X.Y.Z' sencillamente."""
    lv = list(map(int, local.split(".")))
    rv = list(map(int, remote.split(".")))
    return rv > lv

def download_new_exe(download_url):
    """Descarga el .exe remoto a un temp file y devuelve su ruta."""
    resp = requests.get(download_url, stream=True, timeout=30)
    resp.raise_for_status()
    fd, tmp_path = tempfile.mkstemp(suffix=".exe")
    os.close(fd)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(resp.raw, f)
    return tmp_path

def apply_update(new_exe_path):
    """Reemplaza el exe actual y relanza la app."""
    current_exe = sys.executable

    # Renombra el exe viejo por si falla
    old_exe = current_exe + ".old"
    if os.path.exists(old_exe):
        os.remove(old_exe)
    os.rename(current_exe, old_exe)

    # Copia el nuevo en su lugar
    shutil.copy(new_exe_path, current_exe)
    os.chmod(current_exe, 0o755)

    # Lanza la nueva versión y termina esta
    subprocess.Popen([current_exe])
    sys.exit()

def check_for_updates():
    try:
        local_ver = get_local_version()
        data = get_remote_data()
        remote_ver = data["version"]
        download_url = data["url"]

        if is_newer(local_ver, remote_ver):
            print(f"🆕 Nueva versión detectada: {remote_ver} (tú: {local_ver})")
            tmp_exe = download_new_exe(download_url)
            print("⬇️ Descargado nuevo ejecutable, aplicando update…")
            apply_update(tmp_exe)
        else:
            print(f"✔️ Ya tienes la última versión ({local_ver}).")
    except Exception as e:
        print("⚠️ Falló el chequeo de actualización:", e)

if __name__ == "__main__":
    check_for_updates()
