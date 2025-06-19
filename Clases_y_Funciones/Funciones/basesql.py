import sqlite3, hashlib, json
from Clases_y_Funciones.Clases.gestion_recursos import RecursosExternos

# Ruta de la base local compartida
DB_PATH = RecursosExternos.ruta('productos.db')

# ---------- Productos ----------
def init_local_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 1) Crear tabla productos (ahora con precio_compra y precio_total)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            descripcion TEXT,
            precio_compra REAL,
            precio_total REAL
        )
    ''')

    # 2) Migración automática: si faltan las columnas, las añadimos
    cur.execute("PRAGMA table_info(productos)")
    columnas = [row[1] for row in cur.fetchall()]
    if 'precio_compra' not in columnas:
        cur.execute("ALTER TABLE productos ADD COLUMN precio_compra REAL")
    if 'precio_total' not in columnas:
        cur.execute("ALTER TABLE productos ADD COLUMN precio_total REAL")

    # 3) Crear tabla metadata y claves necesarias (igual que antes)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')
    cur.execute("INSERT OR IGNORE INTO metadata(clave, valor) VALUES ('last_count','0')")
    cur.execute("INSERT OR IGNORE INTO metadata(clave, valor) VALUES ('remote_hash','')")

    con.commit()
    con.close()

def get_metadata(clave):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT valor FROM metadata WHERE clave = ?", (clave,))
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

def set_metadata(clave, valor):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE metadata SET valor = ? WHERE clave = ?", (valor, clave))
    con.commit()
    con.close()

def get_local_count():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT valor FROM metadata WHERE clave='last_count'")
    count = int(cur.fetchone()[0])
    con.close()
    return count

def load_local_products():
    """Ahora devuelve listas de código, descripción, precio_compra y precio_total."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT codigo, descripcion, precio_compra, precio_total
        FROM productos
        ORDER BY id
    """)
    productos = cur.fetchall()
    con.close()
    cods    = [c for c,_,_,_ in productos]
    descs   = [d for _,d,_,_ in productos]
    compras = [p for _,_,p,_ in productos]
    totales = [t for _,_,_,t in productos]
    return cods, descs, compras, totales

def save_local_products(items):
    """
    Espera una lista de tuplas (codigo, descripcion, precio_compra, precio_total).
    Reemplaza todos los registros y actualiza metadata.last_count.
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM productos")
    cur.executemany(
        "INSERT INTO productos(codigo, descripcion, precio_compra, precio_total) VALUES (?,?,?,?)",
        items
    )
    cur.execute(
        "UPDATE metadata SET valor = ? WHERE clave = 'last_count'",
        (str(len(items)),)
    )
    con.commit()
    con.close()

def hash_remote_products(coll):
    docs = list(coll.find(
        {},
        {
            "CODIGO": 1,
            "DESCRIPCION DEL PRODUCTO": 1,
            "PRECIO DE COMPRA": 1,
            "PRECIO TOTAL": 1,
            "_id": 0
        }
    ))
    items = []
    for p in docs:
        codigo = str(p.get("CODIGO","")).strip()
        desc   = str(p.get("DESCRIPCION DEL PRODUCTO","")).strip()
        precio = float(p.get("PRECIO DE COMPRA", 0) or 0)
        precio_total = float(p.get("PRECIO TOTAL", 0) or 0)
        items.append((codigo, desc, precio, precio_total))
    items.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    print("[DEBUG hash] primeros items remotos:", items[:5])
    data = json.dumps(items, ensure_ascii=False)
    return hashlib.md5(data.encode('utf-8')).hexdigest()

# ---------- Tasas de Interés (GestionTasas) ----------
def init_local_tasas():
    """
    Crea la tabla 'tasas_interes' con columnas fijas para IVA, tasa anual,
    mensual y cada plazo, e inserta un registro por defecto.
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasas_interes (
            id TEXT PRIMARY KEY,
            iva REAL,
            tasa_interes_anual REAL,
            tasa_interes_mensual REAL,
            plazo_6 REAL,
            plazo_12 REAL,
            plazo_18 REAL,
            plazo_24 REAL,
            plazo_26 REAL
        )
    ''')
    # Inserta fila por defecto si no existe
    cur.execute('''
        INSERT OR IGNORE INTO tasas_interes(
            id, iva, tasa_interes_anual, tasa_interes_mensual,
            plazo_6, plazo_12, plazo_18, plazo_24, plazo_26
        ) VALUES ('tasas_de_interes', 0, 0, 0, 0, 0, 0, 0, 0)
    ''')
    # Metadata para hash de tasas
    cur.execute(
        "INSERT OR IGNORE INTO metadata(clave, valor) VALUES ('tasas_hash', '')"
    )
    con.commit()
    con.close()

def hash_remote_tasas(coll):
    doc = coll.find_one() or {}
    relevant = {
        'iva': doc.get('iva', 0),
        'tasa_interes_anual': doc.get('tasa_interes_anual', 0),
        'tasa_interes_mensual': doc.get('tasa_interes_mensual', 0),
        '6 meses': doc.get('6 meses', 0),
        '12 meses': doc.get('12 meses', 0),
        '18 meses': doc.get('18 meses', 0),
        '24 meses': doc.get('24 meses', 0),
        '26 meses': doc.get('26 meses', 0),
    }
    data = json.dumps(relevant, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def load_local_tasas():
    """
    Devuelve un dict con los valores de tasas_interes;
    keys: iva, anual, mensual, plazo_6, plazo_12, plazo_18, plazo_24, plazo_26
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        'SELECT iva, tasa_interes_anual, tasa_interes_mensual, '
        'plazo_6, plazo_12, plazo_18, plazo_24, plazo_26 '
        'FROM tasas_interes WHERE id = ?',
        ('tasas_de_interes',)
    )
    row = cur.fetchone()
    con.close()
    if not row:
        return {
            'iva': 0,
            'anual': 0.0,
            'mensual': 0.0,
            'plazo_6': 0.0,
            'plazo_12': 0.0,
            'plazo_18': 0.0,
            'plazo_24': 0.0,
            'plazo_26': 0.0,
        }
    return {
        'iva': row[0],
        'anual': row[1],
        'mensual': row[2],
        'plazo_6': row[3],
        'plazo_12': row[4],
        'plazo_18': row[5],
        'plazo_24': row[6],
        'plazo_26': row[7],
    }

def save_local_tasas(tasas: dict):
    """
    Actualiza el registro de tasas_interes con el dict proporcionado.
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''
        UPDATE tasas_interes SET
            iva                 = ?,
            tasa_interes_anual   = ?,
            tasa_interes_mensual = ?,
            plazo_6              = ?,
            plazo_12             = ?,
            plazo_18             = ?,
            plazo_24             = ?,
            plazo_26             = ?
        WHERE id = ?
    ''', (
        tasas.get('iva', 0),
        tasas.get('anual', 0),
        tasas.get('mensual', 0),
        tasas.get('plazo_6', 0),
        tasas.get('plazo_12', 0),
        tasas.get('plazo_18', 0),
        tasas.get('plazo_24', 0),
        tasas.get('plazo_26', 0),
        'tasas_de_interes'
    ))
    con.commit()
    con.close()

# ---------- Spinner Plazos (offline fallback de cuotas) ----------
def save_local_spinner_plazos(plazos):
    """Guarda la lista de plazos en la tabla spinner_plazos."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS spinner_plazos (plazo TEXT PRIMARY KEY)')
    c.execute('DELETE FROM spinner_plazos')
    c.executemany('INSERT INTO spinner_plazos (plazo) VALUES (?)', [(p,) for p in plazos])
    conn.commit()
    conn.close()

def load_local_spinner_plazos():
    """Devuelve lista de plazos guardados localmente."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT plazo FROM spinner_plazos')
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]
