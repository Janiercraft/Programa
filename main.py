import os
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
def main():

    LoginApp().run()

if __name__ == '__main__':
    main()