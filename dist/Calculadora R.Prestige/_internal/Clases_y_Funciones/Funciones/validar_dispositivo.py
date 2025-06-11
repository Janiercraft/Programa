import uuid
from typing import Tuple
from pymongo.errors import PyMongoError
from Clases_y_Funciones.Clases.Conexion_Mongo import Conexion_Mongo
from Clases_y_Funciones.Funciones.usuario_local import (
    guardar_login_local,
    verificar_login_offline
)


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

    # 1) Obtener ID de dispositivo si no se pasó
    if dispositivo_actual is None:
        dispositivo_actual = str(uuid.getnode())

    # 2) Intentar validación online en MongoDB
    try:
        con = Conexion_Mongo(default_db=mongo_db)
        usuarios_col = con.get_collection(collection_name="usuarios")
        planes_col   = con.get_collection(collection_name="planes")

        # 2.1) Buscar el usuario por email
        usuario_doc = usuarios_col.find_one({"email": email_usuario})
        if not usuario_doc:
            con.close()
            return False, "Usuario no encontrado."

        # 2.2) Verificar contraseña (campo “contraseña” en tu colección)
        password_almacenada = usuario_doc.get("contraseña", "")
        if contrasena != password_almacenada:
            con.close()
            return False, "Contraseña incorrecta."

        # 2.3) Obtener dispositivos registrados y plan
        dispositivos_registrados = usuario_doc.get("dispositivos_registrados", [])
        plan_id = usuario_doc.get("plan")
        plan_usuario = planes_col.find_one({"_id": plan_id})
        if not plan_usuario:
            con.close()
            return False, "Error: El plan del usuario no existe en la base de datos."

        max_base  = plan_usuario.get("max_dispositivos", 1)
        max_extra = usuario_doc.get("max_dispositivos_extra", 0)
        total_permitidos = max_base + max_extra

        # 2.4) Si el dispositivo ya estaba registrado
        if dispositivo_actual in dispositivos_registrados:
            # Guardar login local para refrescar fecha de último login online
            guardar_login_local(email_usuario, contrasena)
            con.close()
            return True, "Acceso permitido. Dispositivo ya registrado."

        # 2.5) Si hay espacio para registrar un nuevo dispositivo
        if len(dispositivos_registrados) < total_permitidos:
            dispositivos_registrados.append(dispositivo_actual)
            usuarios_col.update_one(
                {"email": email_usuario},
                {"$set": {"dispositivos_registrados": dispositivos_registrados}}
            )
            # Guardar login local
            guardar_login_local(email_usuario, contrasena)
            con.close()
            return True, f"Dispositivo registrado correctamente ({dispositivo_actual})."

        # 2.6) Si no hay espacio
        con.close()
        return False, "Límite de dispositivos alcanzado. No puedes iniciar sesión desde este dispositivo."

    except (ConnectionError, PyMongoError):
        # 3) Si falla la conexión a Mongo (offline) → ruta offline
        ok_offline, msg_offline = verificar_login_offline(email_usuario, contrasena)
        return ok_offline, msg_offline

    finally:
        # Asegurar que la conexión se cierra en caso de excepción no prevista
        try:
            con.close()
        except Exception:
            pass
