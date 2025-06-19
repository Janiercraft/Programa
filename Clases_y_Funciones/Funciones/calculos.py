from Clases_y_Funciones.Funciones.cliente_mongo import obtener_coleccion_productos
from Clases_y_Funciones.Funciones.basesql import (
    init_local_db,
    load_local_products,
)
from Clases_y_Funciones.Clases.GestionTasas import GestionTasas

_cache_key = None
_cache_compra = 0.0
_cache_total = 0.0

def _obtener_totales_mongo(pares):
    """
    Realiza un pipeline de agregación en Mongo para obtener en un solo paso
    la suma de PRECIO DE COMPRA y PRECIO TOTAL de todos los documentos que coincidan.

    Retorna: (suma_precio_compra, suma_precio_total)

    Si falla (timeout, sin conexión, etc.), propaga excepción para que el caller use el fallback local.
    """
    # 1) Aseguramos que exista la DB local y tablas (pero no forzamos sincronizar aquí)
    init_local_db()

    # 2) Obtenemos la colección desde el cliente persistente
    coll = obtener_coleccion_productos()

    # 3) Construimos el array de condiciones "$or"
    condiciones = []
    for codigo, descripcion in pares:
        if codigo.strip() == "":
            condiciones.append({"DESCRIPCION DEL PRODUCTO": descripcion})
        else:
            condiciones.append({
                "CODIGO": codigo,
                "DESCRIPCION DEL PRODUCTO": descripcion
            })

    # 4) Definimos el pipeline: primero $match, luego $group
    pipeline = [
        {"$match": {"$or": condiciones}},
        {"$group": {
            "_id": None,
            "total_compra": {"$sum": "$PRECIO DE COMPRA"},
            "total_total":  {"$sum": "$PRECIO TOTAL"}
        }}
    ]

    resultado = coll.aggregate(pipeline)
    doc = next(resultado, None)
    if doc is None:
        return 0.0, 0.0

    suma_compra = doc.get("total_compra", 0) or 0
    suma_total  = doc.get("total_total", 0)  or 0
    return float(suma_compra), float(suma_total)


def _fallback_local(pares):
    """
    Fallback a SQLite local si Mongo falla.
    Ahora load_local_products() devuelve cuatro listas:
      cods, descs, compras, totales
    """
    # Desempaquetamos correctamente precios de compra y totales
    cods, descs, compras, totales = load_local_products()

    # Mapas separados para compra y total
    map_compra = {
        (c.strip(), d.strip()): p
        for c, d, p in zip(cods, descs, compras)
    }
    map_total = {
        (c.strip(), d.strip()): t
        for c, d, t in zip(cods, descs, totales)
    }

    suma_compra = 0.0
    suma_total  = 0.0
    for codigo, descripcion in pares:
        key = (codigo.strip(), descripcion.strip())
        suma_compra += map_compra.get(key, 0.0)
        suma_total  += map_total.get(key, 0.0)

    return suma_compra, suma_total


def _get_totales_cached(pares):
    """
    Retorna tuplas (suma_precio_compra, suma_precio_total) usando un cache simple.
    Si 'pares' coincide con la clave anterior, devuelve los valores almacenados.
    En otro caso, intenta obtener de Mongo; si falla, usa fallback local.
    """
    global _cache_key, _cache_compra, _cache_total
    key = tuple(pares)
    if key == _cache_key:
        return _cache_compra, _cache_total

    try:
        suma_compra, suma_total = _obtener_totales_mongo(pares)
    except Exception:
        suma_compra, suma_total = _fallback_local(pares)

    _cache_key = key
    _cache_compra = suma_compra
    _cache_total = suma_total
    return suma_compra, suma_total


def calcular_precio_compra(pares):
    """
    pares: lista de tuplas (codigo, descripcion)
    Devuelve la suma de PRECIO DE COMPRA (o fallback local) usando cache.
    """
    suma_compra, _ = _get_totales_cached(pares)
    return suma_compra


def calcular_precio_total(pares):
    """
    pares: lista de tuplas (codigo, descripcion)
    Devuelve la suma de PRECIO TOTAL (o fallback local) usando cache.
    """
    _, suma_total = _get_totales_cached(pares)
    return suma_total


def saldo_a_financiar(pares, cuota):
    """
    pares: lista de tuplas (codigo, descripcion)
    cuota: número (float)

    Retorna: calcular_precio_total(pares) - cuota, con cache aplicado.
    """
    total = calcular_precio_total(pares)
    try:
        cuota_val = float(cuota)
    except Exception:
        cuota_val = 0.0

    return total - cuota_val

def pago_minimo_mensual(pares, cuota, meses):
    """
    Calcula el pago mínimo mensual para un plazo dado.

    Args:
      pares (list of (str, str)): lista de tuplas (código, descripción).
      cuota (float): monto ya abonado que reduce el saldo a financiar.
      meses (int): plazo en meses (por ejemplo, 6, 12, 18, 24, 26).

    Returns:
      float: valor del pago mínimo mensual (saldo * tasa_plazo/100).

    Raises:
      ValueError: si no se encuentra una tasa para el plazo indicado.
    """
    # 1) Calculamos el saldo a financiar usando tu función existente
    saldo = saldo_a_financiar(pares, cuota)

    # 2) Obtenemos el diccionario de tasas desde Mongo o cache local
    service = GestionTasas(db_name='Royal', collection_name='tasas de interes')
    tasas = service.obtener_tasas()

    # 3) Construimos la clave que coincida con la estructura de tu dict de tasas
    #    en gestion_tasas.py guardas las claves 'plazo_6', 'plazo_12', etc.
    clave = f'plazo_{meses}'
    if clave not in tasas:
        raise ValueError(f"No existe tasa definida para un plazo de {meses} meses")

    porcentaje = tasas[clave]    # por ejemplo 17.82 para 6 meses

    # 4) Pagamos el porcentaje sobre el saldo
    return saldo * (porcentaje / 100.0)