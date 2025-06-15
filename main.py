import os
from pathlib import Path
from Clases_y_Funciones.Clases.gestion_recursos import Recursos, RecursosExternos
from Clases_y_Funciones.Funciones.basesql import init_local_db, init_local_tasas
from Clases_y_Funciones.Funciones.versionsync import VersionSync
from UX.Login import LoginApp

RecursosExternos.init_kivy()

# ——— 2) Sincronizar version.json al directorio de RecursosExternos ———
#    Le pasamos explícitamente la carpeta que ya inicializó RecursosExternos
ext_dir = Path(RecursosExternos._get_dir())
syncer = VersionSync(dir_externo=ext_dir)

if syncer.sync():
    print("[INFO] version.json actualizado en carpeta de recursos externa.")
else:
    print("[INFO] version.json externamente ya estaba al día.")

# 1. Ruta a la base de datos local
DB_PATH = Recursos.ruta('productos.db')

if not os.path.exists(DB_PATH):
    print("[INFO] Base de datos local no encontrada. Creando archivo y esquema...")
else:
    print("[INFO] Base de datos encontrada. Verificando y migrando esquema...")

# Estas llamadas harán CREATE TABLE IF NOT EXISTS y ALTER TABLE
init_local_db()
init_local_tasas()
def main():

    LoginApp().run()

if __name__ == '__main__':
    main()