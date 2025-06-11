import os
from pymongo.errors import PyMongoError
from Clases_y_Funciones.Clases.Conexion_Mongo import Conexion_Mongo
from Clases_y_Funciones.Funciones.basesql import (
    init_local_tasas, load_local_tasas, save_local_tasas,
    get_metadata, set_metadata, hash_remote_tasas
)

class GestionTasas:
    """
    Servicio para cargar las tasas de interés desde MongoDB.

    Uso:
        servicio = GestionTasas(db_name='Royal', collection_name='tasas de interes')
        tasas = servicio.obtener_tasas()
        # tasas['iva'], tasas['anual'], etc.
    """

    def __init__(
        self,
        db_name: str = None,
        collection_name: str = None
    ):
        # Base y colección por defecto desde args o desde .env
        self.db_name         = db_name or os.getenv('MONGO_DB')
        self.collection_name = collection_name or os.getenv('MONGO_COLLECTION')
        # Conector a Mongo
        self._con = Conexion_Mongo(
            default_db=self.db_name,
            default_collection=self.collection_name
        )

    def obtener_tasas(self) -> dict:
        # 1) Asegurar tabla y metadata local
        init_local_tasas()

        try:
            # 2) Hash remoto vs local
            coll = self._con.get_collection()
            new_hash    = hash_remote_tasas(coll)
            saved_hash  = get_metadata('tasas_hash') or ''

            if new_hash != saved_hash:
                # 3) Si cambió: extraer, guardar local y actualizar metadata
                doc = coll.find_one() or {}
                tasas = {
                    'iva':     doc.get('iva', 0),
                    'anual':   doc.get('tasa_interes_anual', 0),
                    'mensual': doc.get('tasa_interes_mensual', 0),
                    'plazo_6': doc.get('6 meses', 0),
                    'plazo_12':doc.get('12 meses',0),
                    'plazo_18':doc.get('18 meses',0),
                    'plazo_24':doc.get('24 meses',0),
                    'plazo_26':doc.get('26 meses',0),
                }
                save_local_tasas(tasas)
                set_metadata('tasas_hash', new_hash)
                return tasas
            else:
                # 4) Sin cambio: carga cache local
                return load_local_tasas()

        except PyMongoError as e:
            # Offline o falla: cargamos localmente
            print(f"[OFFLINE] no puedo cargar tasas de Mongo, uso cache local: {e!r}")
            return load_local_tasas()