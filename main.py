import os
import sys
import json
import threading
import subprocess
import requests
from Clases_y_Funciones.Clases.gestion_recursos import Recursos
from Clases_y_Funciones.Funciones.basesql import init_local_db, init_local_tasas
from UX.Login import LoginApp

# 1. Ruta a la base de datos local
DB_PATH = Recursos.ruta('productos.db')

if not os.path.exists(DB_PATH):
    print("[INFO] Base de datos local no encontrada. Creando archivo y esquema...")
else:
    print("[INFO] Base de datos encontrada. Verificando y migrando esquema...")

# Estas llamadas harán CREATE TABLE IF NOT EXISTS y ALTER TABLE
init_local_db()
init_local_tasas()

def get_app_dir():
    """
    Devuelve la carpeta donde está corriendo la app:
    - En onedir (PyInstaller), sys.executable apunta al .exe dentro de dist/
    - En desarrollo, al directorio del propio .py
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

APP_DIR = get_app_dir()
LOCAL_VER_FILE = os.path.join(APP_DIR, 'version.json')
REPO = "Janiercraft/Programa"  # reemplaza con tu repo

def read_local_version():
    try:
        with open(LOCAL_VER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)['version']
    except Exception:
        return "0.0.0"

def fetch_remote_info():
    """
    Usa gh CLI para obtener tagName y URL del ZIP del último release.
    Requiere haber hecho `gh auth login` previamente.
    """
    # Obtener JSON con tagName y assets[]
    cmd = [
        "gh", "release", "view", "latest",
        "--repo", REPO,
        "--json", "tagName,assets"
    ]
    out = subprocess.check_output(cmd, cwd=APP_DIR).decode()
    data = json.loads(out)
    tag = data['tagName'].lstrip('v')
    # Buscar asset .zip
    zip_asset = next((a for a in data['assets'] if a['name'].endswith('.zip')), None)
    url = zip_asset['browser_download_url'] if zip_asset else None
    return tag, url

def check_update_and_launch():
    local_ver = read_local_version()
    try:
        remote_ver, zip_url = fetch_remote_info()
    except Exception as e:
        print("[UPDATE] No pude consultar gh:", e)
        remote_ver, zip_url = None, None

    if remote_ver and zip_url and remote_ver != local_ver:
        print(f"[UPDATE] Hay nueva versión: {remote_ver} (tienes {local_ver})")
        tmp = os.path.join(APP_DIR, 'update_temp')
        os.makedirs(tmp, exist_ok=True)
        zip_path = os.path.join(tmp, 'app.zip')
        # Descargar ZIP
        with requests.get(zip_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(1024*1024):
                    f.write(chunk)
        # Lanzar updater.py y salir
        updater = os.path.join(APP_DIR, 'updater.py')
        subprocess.Popen([sys.executable, updater, tmp], cwd=APP_DIR)
        sys.exit(0)  # termina la instancia actual para que updater reemplace

def main():
    # Lanzamos el chequeo de actualización en segundo plano antes del login
    threading.Thread(target=check_update_and_launch, daemon=True).start()
    # Inicia tu app Kivy
    LoginApp().run()

if __name__ == '__main__':
    main()
