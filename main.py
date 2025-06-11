import os
import sys
import actualizador
from UX.Login import LoginApp
from Clases_y_Funciones.Clases.gestion_recursos import Recursos
from Clases_y_Funciones.Funciones.basesql import init_local_db, init_local_tasas

def main():
    # 0.1 Lanza el updater; si hay update/rollback hará sys.exit()
    try:
        actualizador.check_for_updates()
    except SystemExit:
        # El updater ya reinició o salió tras rollback
        sys.exit()

    DB_PATH = Recursos.ruta('productos.db')

    if not os.path.exists(DB_PATH):
        print("[INFO] Base de datos local no encontrada. Creando archivo y esquema...")
    else:
        print("[INFO] Base de datos encontrada. Verificando y migrando esquema...")

    init_local_db()
    init_local_tasas()

    # 2. Lanza la interfaz de Login
    
    LoginApp().run()

if __name__ == "__main__":
    main()
