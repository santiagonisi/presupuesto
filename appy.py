from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Conectar a la base de datos
def obtener_conexion():
    conn = sqlite3.connect('empresa.db')
    conn.row_factory = sqlite3.Row  # Acceder a las filas por nombre de columna
    return conn

# Crear las tablas al iniciar la aplicación
def crear_tablas():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS centros_costos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        departamento TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        razonsocial TEXT NOT NULL,
        contacto TEXT NOT NULL,
        cuit TEXT NOT NULL,
        rubro TEXT NOT NULL,
        ubicacion TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        cantidad INTEGER NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proveedores_productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        precio REAL NOT NULL,
        fecha TEXT,
        centro_costo_id INTEGER,
        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
        FOREIGN KEY (producto_id) REFERENCES productos(id),
        FOREIGN KEY (centro_costo_id) REFERENCES centros_costos(id)
    )
    ''')
    conn.commit()
    conn.close()

crear_tablas()

# Página principal
@app.route('/')
def index():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT pp.fecha, pr.nombre AS producto, pp.precio, p.nombre AS proveedor, cc.nombre AS centro_costo
    FROM proveedores_productos pp
    JOIN proveedores p ON pp.proveedor_id = p.id
    JOIN productos pr ON pp.producto_id = pr.id
    JOIN centros_costos cc ON pp.centro_costo_id = cc.id
    ''')
    presupuestos = cursor.fetchall()
    conn.close()
    return render_template('index.html', presupuestos=presupuestos)

# Agregar un presupuesto
@app.route('/agregar_presupuesto', methods=['GET', 'POST'])
def agregar_presupuesto():
    if request.method == 'POST':
        proveedor_id = request.form['proveedor_id']
        producto_id = request.form['producto_id']
        precio = request.form['precio']
        fecha = request.form['fecha']
        centro_costo_id = request.form['centro_costo_id']
        
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO proveedores_productos (proveedor_id, producto_id, precio, fecha, centro_costo_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (proveedor_id, producto_id, precio, fecha, centro_costo_id))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM proveedores')
    proveedores = cursor.fetchall()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    cursor.execute('SELECT * FROM centros_costos')
    centros_costos = cursor.fetchall()
    conn.close()

    return render_template('agregar_presupuesto.html', proveedores=proveedores, productos=productos, centros_costos=centros_costos)

if __name__ == '__main__':
    app.run(debug=True)
    