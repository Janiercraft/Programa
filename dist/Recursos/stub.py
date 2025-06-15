import os
import sys
import shutil
import tempfile
import time
import subprocess
import requests
from tqdm import tqdm
import json

# URL de tu version.json público en GitHub
REMOTE_VERSION_JSON = "https://raw.githubusercontent.com/Janiercraft/Programa/main/version.json"

def download_with_progress(url, dest_path):
    resp = requests.get(url, stream=True, timeout=15)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    print("Descargando actualización…")
    with open(dest_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, leave=False) as bar:
        for chunk in resp.iter_content(chunk_size=8192):
            if not chunk:
                break
            f.write(chunk)
            bar.update(len(chunk))

def main():
    # --- 1) Rutas dinámicas basadas en dónde esté este stub.exe ---
    stub_path    = sys.executable
    recursos_dir = os.path.dirname(stub_path)
    parent_dir   = os.path.dirname(recursos_dir)
    local_vjson  = os.path.join(recursos_dir, "version.json")

    # --- 2) Limpieza de carpetas temporales viejas ---
    for name in os.listdir(recursos_dir):
        if name.startswith("updater_"):
            dirpath = os.path.join(recursos_dir, name)
            if os.path.isdir(dirpath):
                shutil.rmtree(dirpath, ignore_errors=True)

    # --- 3) Nombre fijo de la app a actualizar ---
    TARGET_NAME = "Calculadora R.Prestige.exe"
    target_exe  = os.path.join(parent_dir, TARGET_NAME)
    backup_exe  = target_exe + ".old"

    if not os.path.isfile(target_exe):
        print(f"❌ No encontré '{TARGET_NAME}' en {parent_dir}")
        sys.exit(1)

    # --- 4) Leer versión local ---
    try:
        with open(local_vjson, "r", encoding="utf-8") as f:
            local_info = json.load(f)
        local_version = local_info.get("version")
    except Exception as e:
        print("❌ Error al leer version.json local:", e)
        sys.exit(1)

    # --- 5) Leer versión remota en memoria ---
    try:
        resp = requests.get(REMOTE_VERSION_JSON, timeout=10)
        resp.raise_for_status()
        remote_info    = resp.json()
        remote_version = remote_info.get("version")
        remote_url     = remote_info.get("url")
    except Exception as e:
        print("❌ No pude obtener version.json remoto:", e)
        # Si falla, arranca la versión que hay instalada
        subprocess.Popen([target_exe], cwd=parent_dir)
        sys.exit(0)

    # --- 6) Comparar versiones ---
    if remote_version == local_version:
        print(f"✔ Ya tienes la versión más reciente ({local_version})")
        subprocess.Popen([target_exe], cwd=parent_dir)
        sys.exit(0)
    else:
        print(f"🔄 Actualizando: {local_version} → {remote_version}")

    # --- 7) URL remota para descargar ---
    download_url = remote_url

    # --- 8) Crear carpeta temporal en recursos/ ---
    tmpdir = tempfile.mkdtemp(prefix="updater_", dir=recursos_dir)
    new_exe = os.path.join(tmpdir, TARGET_NAME)

    try:
        # --- 9) Descargar el nuevo exe ---
        download_with_progress(download_url, new_exe)

        # --- 10) Asegurar cierre de la app original ---
        time.sleep(0.5)

        # --- 11) Backup y reemplazo ---
        if os.path.exists(backup_exe):
            os.remove(backup_exe)
        os.rename(target_exe, backup_exe)
        shutil.move(new_exe, target_exe)
        print("Actualización completada ✅")

        # --- 12) Limpieza completa SOLO tras éxito ---
        shutil.rmtree(tmpdir, ignore_errors=True)
        if os.path.exists(backup_exe):
            os.remove(backup_exe)

        # --- 13) Arrancar la app actualizada (sin flags) ---
        subprocess.Popen([target_exe], cwd=parent_dir)

    except Exception as e:
        print("❌ Error en la actualización:", e)
        # Rollback si algo falla
        if os.path.exists(backup_exe) and not os.path.exists(target_exe):
            os.rename(backup_exe, target_exe)
            print("⚠ Rollback realizado: restaurada la versión anterior.")
        subprocess.Popen([target_exe], cwd=parent_dir)

    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
