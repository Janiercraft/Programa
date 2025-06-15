#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
import time
import subprocess
import requests
from tqdm import tqdm
import json

# RAW URL de tu version.json en GitHub
REMOTE_VERSION_JSON = "https://raw.githubusercontent.com/Janiercraft/Programa/main/version.json"

def download_with_progress(url, dest_path):
    resp = requests.get(url, stream=True, timeout=15)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    print("Descargando actualización…")
    with open(dest_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, leave=False) as bar:
        for chunk in resp.iter_content(8192):
            if not chunk:
                break
            f.write(chunk)
            bar.update(len(chunk))

def main():
    # Sólo respondemos al flag --update
    if "--update" not in sys.argv:
        print("Use --update para iniciar el proceso de actualización.")
        sys.exit(1)

    stub_path    = sys.executable
    recursos_dir = os.path.dirname(stub_path)
    parent_dir   = os.path.dirname(recursos_dir)

    TARGET_NAME = "Calculadora R.Prestige.exe"
    target_exe  = os.path.join(parent_dir, TARGET_NAME)
    backup_exe  = target_exe + ".old"

    # 1) Leer JSON remoto para obtener URL
    try:
        r = requests.get(REMOTE_VERSION_JSON, timeout=10)
        r.raise_for_status()
        info = r.json()
        download_url = info["url"]
    except Exception as e:
        print("❌ No pude leer version.json remoto:", e)
        # Arrancar la app y salir
        subprocess.Popen([target_exe], cwd=parent_dir)
        sys.exit(0)

    # 2) Preparar carpeta temporal
    tmpdir = tempfile.mkdtemp(prefix="updater_", dir=recursos_dir)
    new_exe = os.path.join(tmpdir, TARGET_NAME)

    try:
        # 3) Descargar
        download_with_progress(download_url, new_exe)
        time.sleep(0.5)

        # 4) Backup y swap
        if os.path.exists(backup_exe):
            os.remove(backup_exe)
        os.rename(target_exe, backup_exe)
        shutil.move(new_exe, target_exe)
        print("Actualización completada ✅")

        # 5) Limpieza
        shutil.rmtree(tmpdir, ignore_errors=True)
        if os.path.exists(backup_exe):
            os.remove(backup_exe)

        # 6) Lanzar app
        subprocess.Popen([target_exe], cwd=parent_dir)

    except Exception as e:
        print("❌ Error en la actualización:", e)
        # rollback
        if os.path.exists(backup_exe) and not os.path.exists(target_exe):
            os.rename(backup_exe, target_exe)
            print("⚠ Rollback realizado.")
        subprocess.Popen([target_exe], cwd=parent_dir)

    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()
