from Clases_y_Funciones.Clases.Conexion_Mongo import Conexion_Mongo

# Creamos un cliente Mongo al importar este módulo.
# Este objeto vive durante todo el ciclo de vida de la app.
_mongo_conexion = Conexion_Mongo(default_db='Royal', default_collection='productos')

def obtener_coleccion_productos():
    """
    Retorna la colección 'productos' usando el cliente persistente.
    """
    return _mongo_conexion.get_collection()

def cerrar_conexion():
    """
    Si en algún punto necesitas cerrar manualmente (por ejemplo, al apagar la app),
    puedes llamar esto. Por lo demás, no es obligatorio.
    """
    try:
        _mongo_conexion.close()
    except:
        pass