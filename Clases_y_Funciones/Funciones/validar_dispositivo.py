import hashlib
import uuid
import platform
import subprocess
from typing import Tuple
from pymongo.errors import PyMongoError
from Clases_y_Funciones.Clases.Conexion_Mongo import Conexion_Mongo
from Clases_y_Funciones.Funciones.usuario_local import (
    guardar_login_local,
    verificar_login_offline
)


def obtener_machine_id() -> str:
    """
    Obtiene un identificador único del sistema operativo:
    - Linux: /etc/machine-id o /var/lib/dbus/machine-id
    - Windows: registro MachineGuid
    - macOS (Darwin): IOPlatformUUID
    Si no está disponible, retorna cadena vacía.
    """
    so = platform.system()
    try:
        if so == "Linux":
            for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
                try:
                    with open(path, "r") as f:
                        val = f.read().strip()
                        if val:
                            return val
                except FileNotFoundError:
                    continue
        elif so == "Windows":
            # lee desde el registro MachineGuid
            cmd = ["reg", "query",
                   r"HKLM\SOFTWARE\Microsoft\Cryptography",
                   "/v", "MachineGuid"]
            salida = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return salida.strip().split()[-1]
        elif so == "Darwin":  # macOS
            cmd = ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
            salida = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            for line in salida.splitlines():
                if "IOPlatformUUID" in line:
                    return line.split('=')[1].strip().strip('"')
    except Exception:
        pass
    return ""


def obtener_fingerprint_hw() -> str:
    """
    Genera un fingerprint estable basado en machine-id del SO.
    Si no está disponible, hace fallback a uuid.getnode().
    Siempre devuelve un SHA-256 hexdigest de ese valor.
    """
    mid = obtener_machine_id()
    if mid:
        raw = mid
    else:
        # Fallback: utiliza el MAC (getnode) o nodo del host
        try:
            raw = str(uuid.getnode())
        except Exception:
            raw = platform.node()
    return hashlib.sha256(raw.encode()).hexdigest()


def validar_credenciales_y_dispositivo(
    email_usuario: str,
    contrasena: str,
    dispositivo_actual: str = None,
    mongo_db: str = "Royal"
) -> Tuple[bool, str]:
    """
    1) Si hay Internet:
         - Valida usuario+contraseña en MongoDB.
         - Controla límite de dispositivos:
             • Si ya estaba registrado → éxito online.
             • Si cabe un dispositivo más → registra en Mongo y éxito online.
             • Si excede el límite → error online.
         - En caso de éxito online, guarda login local para modo offline.
    2) Si NO hay Internet (o falla la conexión a Mongo):
         - Llama a verificar_login_offline(usuario, contrasena):
             • Si retorna True → éxito offline.
             • Si retorna False → error offline (ya incluye mensaje).
    """

    # 1) Obtener fingerprint si no se pasó explícitamente
    if dispositivo_actual is None:
        dispositivo_actual = obtener_fingerprint_hw()

    # 2) Intentar validación online en MongoDB
    try:
        con = Conexion_Mongo(default_db=mongo_db)
        usuarios_col = con.get_collection(collection_name="usuarios")
        planes_col   = con.get_collection(collection_name="planes")

        usuario_doc = usuarios_col.find_one({"email": email_usuario})
        if not usuario_doc:
            con.close()
            return False, "Usuario no encontrado."

        if contrasena != usuario_doc.get("contraseña", ""):
            con.close()
            return False, "Contraseña incorrecta."

        dispositivos_registrados = usuario_doc.get("dispositivos_registrados", [])
        plan_doc = planes_col.find_one({"_id": usuario_doc.get("plan")})
        if not plan_doc:
            con.close()
            return False, "Error: el plan del usuario no existe."

        total_permitidos = plan_doc.get("max_dispositivos", 1) + usuario_doc.get("max_dispositivos_extra", 0)

        if dispositivo_actual in dispositivos_registrados:
            guardar_login_local(email_usuario, contrasena)
            con.close()
            return True, "Acceso permitido."

        if len(dispositivos_registrados) < total_permitidos:
            dispositivos_registrados.append(dispositivo_actual)
            usuarios_col.update_one(
                {"email": email_usuario},
                {"$set": {"dispositivos_registrados": dispositivos_registrados}}
            )
            guardar_login_local(email_usuario, contrasena)
            con.close()
            return True, f"Dispositivo registrado correctamente ({dispositivo_actual})."

        con.close()
        return False, "Límite de dispositivos alcanzado."

    except (ConnectionError, PyMongoError):
        return verificar_login_offline(email_usuario, contrasena)

    finally:
        try:
            con.close()
        except Exception:
            pass
