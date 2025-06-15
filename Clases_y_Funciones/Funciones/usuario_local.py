import os
import sqlite3
import bcrypt
import base64
import hashlib
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from Clases_y_Funciones.Clases.gestion_recursos import RecursosExternos

# Ruta absoluta para usuarios.db (en la carpeta de Recursos)
DB_PATH = RecursosExternos.ruta("usuarios.db")

# === 1. Clave Fernet derivada del usuario ===
def generar_clave_fernet(usuario: str) -> bytes:
    """
    Deriva una clave de 32 bytes a partir del nombre de usuario usando SHA-256,
    luego la codifica a base64-url para que sirva como clave de Fernet.
    """
    sha = hashlib.sha256(usuario.encode()).digest()      # 32 bytes
    return base64.urlsafe_b64encode(sha)                 # Forma que Fernet acepta

def cifrar_fecha(fecha_str: str, usuario: str) -> str:
    """
    Cifra la fecha (en texto ISO) con Fernet, usando la clave derivada del usuario.
    Retorna la fecha cifrada en base64 (texto).
    """
    f = Fernet(generar_clave_fernet(usuario))
    return f.encrypt(fecha_str.encode()).decode()

def descifrar_fecha(fecha_cifrada: str, usuario: str) -> str:
    """
    Intenta descifrar la fecha cifrada. Si falla (clave incorrecta, datos corruptos), retorna None.
    """
    try:
        f = Fernet(generar_clave_fernet(usuario))
        return f.decrypt(fecha_cifrada.encode()).decode()
    except Exception:
        return None

# === 2. Inicialización de la base de datos local ===
def init_db():
    """
    Crea (si no existe) la tabla 'usuarios' con columnas:
      - usuario           : nombre de usuario (texto plano, único)
      - hash_contrasena   : bcrypt hash de la contraseña
      - fecha_login_cifrada: fecha (ISO) cifrada con Fernet
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            hash_contrasena TEXT,
            fecha_login_cifrada TEXT
        )
    ''')
    con.commit()
    con.close()

# === 3. Guardar el último login online en local ===
def guardar_login_local(usuario: str, contrasena: str):
    """
    Reemplaza cualquier registro previo por uno nuevo:
    - Hashea la contraseña con bcrypt.
    - Cifra la fecha actual (UTC) con la clave derivada del usuario.
    - Inserta (usuario, hash_contrasena, fecha_cifrada) en la tabla.
    """
    init_db()
    # 3.1. Hashear la contraseña
    hash_pw = bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()
    # 3.2. Fecha actual en ISO (UTC)
    fecha_actual = datetime.utcnow().isoformat()
    # 3.3. Cifrar la fecha
    fecha_cifrada = cifrar_fecha(fecha_actual, usuario)

    # 3.4. Reemplazar el registro anterior (borramos todos, porque solo permitimos 1 usuario local)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM usuarios")
    cur.execute(
        "INSERT INTO usuarios (usuario, hash_contrasena, fecha_login_cifrada) VALUES (?, ?, ?)",
        (usuario, hash_pw, fecha_cifrada)
    )
    con.commit()
    con.close()

# === 4. Verificar login en modo offline ===
def verificar_login_offline(usuario: str, contrasena: str):
    init_db()

    # 4.1. Comprobar que exista la BD
    if not os.path.isfile(DB_PATH):
        return False, "No hay datos locales."

    # 4.2. Leer el registro para este usuario
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT hash_contrasena, fecha_login_cifrada FROM usuarios WHERE usuario = ?",
        (usuario,)
    )
    row = cur.fetchone()
    con.close()

    if not row:
        return False, "No hay datos locales para este usuario."

    hash_pw, fecha_cifrada = row

    # 4.3. Verificar contraseña con bcrypt
    if not bcrypt.checkpw(contrasena.encode(), hash_pw.encode()):
        return False, "Contraseña incorrecta"

    # 4.4. Descifrar la fecha
    fecha_descifrada = descifrar_fecha(fecha_cifrada, usuario)
    if not fecha_descifrada:
        eliminar_db_local()  # si no se puede descifrar, borramos la base local
        return False, "No se pudo validar la fecha local. Eliminando datos locales."

    # 4.5. Convertir a datetime y comparar
    try:
        fecha_dt = datetime.fromisoformat(fecha_descifrada)
    except ValueError:
        # Fecha malformada → eliminar la base de datos local
        eliminar_db_local()
        return False, "Fecha local inválida. Eliminando datos locales."

    if datetime.utcnow() - fecha_dt > timedelta(days=3):
        eliminar_db_local()
        return False, "Credenciales locales expiraron. Conéctate a Internet para renovar acceso."

    return True, "Acceso permitido."

# === 5. Eliminar la base de datos local ===
def eliminar_db_local():
    """
    Borra el archivo 'usuarios.db' si existe.
    Se usa cuando las credenciales exceden los 3 días o la fecha está corrupta.
    """
    if os.path.isfile(DB_PATH):
        os.remove(DB_PATH)