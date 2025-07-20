import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def load_env():
    """
    Carga el archivo .env desde:
      - la carpeta temporal de PyInstaller (sys._MEIPASS) si estamos en un exe --onefile
      - o desde el directorio del script si estamos en desarrollo.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    # Determinar base_path según entorno
    if getattr(sys, 'frozen', False):
        # Ejecutable PyInstaller
        base_path = sys._MEIPASS
    else:
        # Ejecución normal (fuente)
        base_path = os.path.abspath(os.path.dirname(__file__))

    env_path = os.path.join(base_path, '.env')
    load_dotenv(dotenv_path=env_path)


class Conexion_Mongo:
    """
    Clase reutilizable para conectar y operar con MongoDB Atlas.

    Variables de entorno soportadas en .env o en el entorno del sistema:
      - MONGO_URI              (obligatoria)
      - MONGO_DB               (obligatoria si no se pasa default_db)
      - MONGO_COLLECTION       (opcional si no se pasa default_collection)
      - MONGO_SERVER_SELECTION_TIMEOUT_MS
      - MONGO_CONNECT_TIMEOUT_MS
      - MONGO_SOCKET_TIMEOUT_MS
      - MONGO_CONNECT_ON_INIT  (0 o 1)
    """

    def __init__(
        self,
        uri: str = None,
        default_db: str = None,
        default_collection: str = None
    ):
        # Cargar .env si existe
        load_env()

        # Leer configuración
        self.uri              = uri or os.getenv('MONGO_URI')
        self.default_db       = default_db or os.getenv('MONGO_DB')
        self.default_collection = default_collection or os.getenv('MONGO_COLLECTION')

        if not self.uri:
            raise ValueError("Falta MONGO_URI en entorno o argumento `uri`.")
        if not self.default_db:
            raise ValueError("Falta MONGO_DB en entorno o argumento `default_db`.")

        # Timeouts (milisegundos), con valores por defecto
        self.server_selection_timeout_ms = int(os.getenv('MONGO_SERVER_SELECTION_TIMEOUT_MS', 500))
        self.connect_timeout_ms          = int(os.getenv('MONGO_CONNECT_TIMEOUT_MS', 500))
        self.socket_timeout_ms           = int(os.getenv('MONGO_SOCKET_TIMEOUT_MS', 500))
        self.connect_on_init             = bool(int(os.getenv('MONGO_CONNECT_ON_INIT', 1)))

        self._client = None
        if self.connect_on_init:
            self._connect()

    def _connect(self):
        try:
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                connectTimeoutMS=self.connect_timeout_ms,
                socketTimeoutMS=self.socket_timeout_ms
            )
            # Verificar conexión rápida
            self._client.admin.command('ping')
        except ConnectionFailure as e:
            self._client = None
            raise ConnectionError(f"No se pudo conectar a MongoDB: {e}")

    def get_database(self, db_name: str = None):
        name = db_name or self.default_db
        if not name:
            raise ValueError("Debe especificar db_name o configurar MONGO_DB.")
        if not self._client:
            self._connect()
        return self._client[name]

    def get_collection(self, collection_name: str = None, db_name: str = None):
        name = collection_name or self.default_collection
        if not name:
            raise ValueError("Debe especificar collection_name o configurar MONGO_COLLECTION.")
        db = self.get_database(db_name)
        return db[name]

    def insert_one(self, document: dict, collection_name: str = None, db_name: str = None):
        return self.get_collection(collection_name, db_name).insert_one(document)

    def find(self, filter: dict, collection_name: str = None, db_name: str = None, *, limit: int = 0):
        cursor = self.get_collection(collection_name, db_name).find(filter)
        return list(cursor.limit(limit)) if limit else list(cursor)

    def update_one(self, filter: dict, update: dict, collection_name: str = None, db_name: str = None):
        return self.get_collection(collection_name, db_name).update_one(filter, {'$set': update})

    def delete_one(self, filter: dict, collection_name: str = None, db_name: str = None):
        return self.get_collection(collection_name, db_name).delete_one(filter)

    def close(self):
        """
        Cierra la conexión al servidor MongoDB si existe.
        """
        if self._client:
            self._client.close()
            self._client = None


if __name__ == '__main__':
    con = Conexion_Mongo(default_db='Royal', default_collection='productos')
    coll = con.get_collection()
    print("Documentos en productos:", coll.count_documents({}))
    con.close()
