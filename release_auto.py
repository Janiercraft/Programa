import os
import sys
import json
import subprocess

# CONFIGURA ESTO 🔧
REPO = "Janiercraft/Programa"  # ← Cambia a tu repo real
VERSION_FILE = "version.json"
EXE_PATH = "dist/Calculadora R.Prestige.exe"
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

# 🔢 Incrementar versión en esquema decimal (0–9) con carry
def increment_version(version, tipo="patch", base=10):
    """
    - patch: sube patch; al llegar a base, resetea y bump minor.
    - minor: sube minor; resetea patch; al llegar a base, resetea y bump major.
    - major: sube major; resetea minor y patch.
    """
    try:
        major, minor, patch = map(int, version.split("."))
    except ValueError:
        raise ValueError(f"Versión inválida: '{version}'. Debe ser 'X.Y.Z' con enteros")

    if tipo == "patch":
        patch += 1
        if patch >= base:
            patch = 0
            minor += 1
    elif tipo == "minor":
        minor += 1
        patch = 0
    elif tipo == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Tipo de incremento inválido: {tipo}")

    # Carry para minor → major
    if minor >= base:
        minor = 0
        major += 1

    return f"{major}.{minor}.{patch}"

# 📤 Guardar nueva versión y URL en version.json
def save_version_data(version, url):
    with open(VERSION_FILE, "w") as f:
        json.dump({"version": version, "url": url}, f, indent=2)
    print(f"📝 version.json actualizado:\n - version: {version}\n - url: {url}")

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
    tag = f"v{version}"
    return f"https://github.com/{REPO}/releases/download/{tag}/{EXE_NOMBRE}"

# 🏁 Main
if __name__ == "__main__":
    # 1. Cargar versión actual
    version_data = load_version_data()
    old_version = version_data["version"]

    # 2. Calcular nueva versión
    new_version = increment_version(old_version, tipo="patch")

    # 3. Mostrar en consola y pedir confirmación
    print(f"🔄 Versión actual: {old_version}")
    print(f"⬆️  Nueva versión: {new_version}")
    respuesta = input("¿Deseas continuar con el release? (Y/N): ").strip().upper()
    if respuesta != "Y":
        print("🚫 Operación cancelada.")
        sys.exit(0)

    # 4. Crear release y actualizar version.json
    nueva_url = generar_url(new_version)
    notas = f"Auto-release generada para la versión {new_version}."

    crear_release(new_version, notas)
    save_version_data(new_version, nueva_url)
