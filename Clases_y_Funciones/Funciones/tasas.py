from Clases_y_Funciones.Clases.Conexion_Mongo import Conexion_Mongo
from Clases_y_Funciones.Funciones.basesql import init_local_db, load_local_spinner_plazos, save_local_spinner_plazos

def obtener_plazos_meses():
    """
    Lee el documento de tasas_de_interes en Mongo Atlas,
    extrae todas las claves que terminen en 'meses' y devuelve 
    una lista de strings. Si falla, cae al local de spinner_plazos.
    """
    init_local_db()  # crea la DB si no existe
    try:
        con = Conexion_Mongo(default_db='Royal', default_collection='tasas de interes')
        doc = con.get_collection().find_one({'id': 'tasas_de_interes'})
        con.close()
        plazos = [k for k in doc.keys() if k.endswith('meses')]
        save_local_spinner_plazos(plazos)
    except Exception:
        plazos = load_local_spinner_plazos()
    return plazos
