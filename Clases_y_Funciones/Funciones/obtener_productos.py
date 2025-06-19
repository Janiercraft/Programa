from Clases_y_Funciones.Funciones.basesql import (
init_local_db, load_local_products, get_local_count,
get_metadata, hash_remote_products, save_local_products,
set_metadata)
from Clases_y_Funciones.Clases.Conexion_Mongo import Conexion_Mongo

def obtener_datos_productos():
    init_local_db()

    # 1) Carga inmediata de lo local
    cods, descs, precios, precios_total = load_local_products()
    local_count = get_local_count()
    print(f"[DEBUG] Local count = {local_count}, loaded {len(cods)} rows")

    try:
        con = Conexion_Mongo(default_db='Royal', default_collection='productos')
        coll = con.get_collection()

        # 2) Chequeo de hash remoto
        nuevo_hash   = hash_remote_products(coll)
        hash_guardado = get_metadata('remote_hash')
        print(f"[DEBUG] Hash remoto = {nuevo_hash}, guardado = {hash_guardado}")

        if nuevo_hash != hash_guardado:
            print("[DEBUG] Colección cambió → sincronizando...")
            docs = coll.find(
                {},
                {
                    "CODIGO": 1,
                    "DESCRIPCION DEL PRODUCTO": 1,
                    "PRECIO DE COMPRA": 1,
                    "PRECIO TOTAL": 1,
                    "_id": 0
                }
            )
            items = []
            for p in docs:
                codigo = str(p.get("CODIGO","")).strip()
                desc   = str(p.get("DESCRIPCION DEL PRODUCTO","")).strip()
                precio = float(p.get("PRECIO DE COMPRA",0) or 0)
                precio_total = float(p.get("PRECIO TOTAL", 0) or 0)  # <- nuevo campo
                items.append((codigo, desc, precio, precio_total))

            save_local_products(items)
            set_metadata('remote_hash', nuevo_hash)
            print(f"[DEBUG] Guardados {len(items)} productos con precio y actualizado remote_hash")
        else:
            print("[DEBUG] Sin cambios en colección, uso datos locales.")
    except Exception as e:
        print(f"[OFFLINE] No puedo conectar o hash falló: {e!r}")

    # 3) Siempre devolvemos lo local (ahora con precios)
    return load_local_products()