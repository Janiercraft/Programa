import os
import sys
import json
import subprocess
import semver

# CONFIGURA ESTO 🔧
REPO = "tuusuario/turepo"  # ← Cambia a tu repo real
VERSION_FILE = "version.json"
EXE_PATH = "dist/MiApp.exe"
EXE_NOMBRE = os.path.basename(EXE_PATH)

# 📥 Cargar datos de versión
def load_version_data():
    if not os.path.exists(VERSION_FILE):
        print(f"❌ No se encontró {VERSION_FILE}")
        sys.exit(1)

    with open(VERSION_FILE, "r") as f:
        data = json.load(f)

    if "version" not in data or "url" not in data:
        print("❌ El archivo version.json debe contener 'version' y 'url'")
        sys.exit(1)

    return data

# 📤 Guardar nueva versión y URL en version.json
def save_version_data(version, url):
    with open(VERSION_FILE, "w") as f:
        json.dump({"version": version, "url": url}, f, indent=2)
    print(f"📝 version.json actualizado:\n - version: {version}\n - url: {url}")

# 🔢 Incrementar versión (patch por defecto)
def increment_version(version, tipo="patch"):
    v = semver.Version.parse(version)
    if tipo == "patch":
        return v.bump_patch()
    elif tipo == "minor":
        return v.bump_minor()
    elif tipo == "major":
        return v.bump_major()
    else:
        raise ValueError("Tipo de incremento inválido")

# 🚀 Crear release en GitHub
def crear_release(version, notas):
    tag = f"v{version}"
    print(f"📦 Creando release {tag}...")

    if not os.path.isfile(EXE_PATH):
        print(f"❌ No se encontró el ejecutable en: {EXE_PATH}")
        sys.exit(1)

    comando = [
        "gh", "release", "create", tag,
        EXE_PATH,
        "--repo", REPO,
        "--title", f"Versión {version}",
        "--notes", notas
    ]

    try:
        subprocess.run(comando, check=True)
        print("✅ Release creada con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear la release: {e}")
        sys.exit(1)

# 🧠 Generar nueva URL para la descarga
def generar_url(version):
    user_repo = REPO
    tag = f"v{version}"
    return f"https://github.com/{user_repo}/releases/download/{tag}/{EXE_NOMBRE}"

# 🏁 Main
if __name__ == "__main__":
    version_data = load_version_data()
    old_version = version_data["version"]

    new_version = str(increment_version(old_version, tipo="patch"))

    print(f"🔄 Versión {old_version} → {new_version}")

    nueva_url = generar_url(new_version)
    notas = f"Auto-release generada para la versión {new_version}."

    crear_release(new_version, notas)
    save_version_data(new_version, nueva_url)
