import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Configuración de la carpeta de subida
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Asegura que la carpeta exista
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Conectar a la base de datos
def obtener_conexion():
    conn = sqlite3.connect('empresa.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row  
    return conn

# Crear las tablas
def crear_tablas():
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS centros_costos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        departamento TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        razonsocial TEXT,
        contacto TEXT,
        cuit TEXT,
        rubro TEXT,
        ubicacion TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        categoria TEXT,
        cantidad INTEGER DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proveedores_productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        precio REAL NOT NULL,
        fecha TEXT NOT NULL,
        centro_costo_id INTEGER NOT NULL,
        pdf_path TEXT,
        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
        FOREIGN KEY (producto_id) REFERENCES productos(id),
        FOREIGN KEY (centro_costo_id) REFERENCES centros_costos(id)
    )
    ''')

    conn.commit()
    conn.close()

# Insertar centros de costos si no existen
def insertar_centros_costos():
    conn = obtener_conexion()
    cursor = conn.cursor()

    centros_costos = [
        ('Sector Obra', 'Obra'),
        ('Sector Administración', 'Administración'),
        ('Sector Oficina Técnica', 'Oficina Técnica'),
        ('Sector Laboratorio', 'Laboratorio'),
        ('Sector Mantenimiento', 'Mantenimiento'),
        ('Sector Seguridad y Medio Ambiente', 'Seguridad y Medio Ambiente'),
        ('Planta Ramallo', 'Planta'),
        ('Planta Baradero', 'Planta'),
        ('Planta Hormigón', 'Planta')
    ]

    for nombre, departamento in centros_costos:
        cursor.execute('SELECT id FROM centros_costos WHERE nombre = ?', (nombre,))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO centros_costos (nombre, departamento) VALUES (?, ?)', (nombre, departamento))

    conn.commit()
    conn.close()

# Página principal con listado de presupuestos
@app.route('/')
def index():
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT pp.fecha, p.nombre AS proveedor, pr.nombre AS producto, pp.precio, cc.nombre AS centro_costo, pp.pdf_path
    FROM proveedores_productos pp
    JOIN proveedores p ON pp.proveedor_id = p.id
    JOIN productos pr ON pp.producto_id = pr.id
    JOIN centros_costos cc ON pp.centro_costo_id = cc.id
    ''')
    presupuestos = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', presupuestos=presupuestos)

# Página de proveedores
@app.route('/proveedores')
def proveedores():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM proveedores')
    proveedores = cursor.fetchall()
    conn.close()
    return render_template('proveedores.html', proveedores=proveedores)

# Agregar proveedor
@app.route('/agregar_proveedor', methods=['POST'])
def agregar_proveedor():
    nombre = request.form['nombre']
    razonsocial = request.form['razonsocial']
    contacto = request.form['contacto']
    cuit = request.form['cuit']
    rubro = request.form['rubro']
    ubicacion = request.form['ubicacion']

    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO proveedores (nombre, razonsocial, contacto, cuit, rubro, ubicacion)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nombre, razonsocial, contacto, cuit, rubro, ubicacion))
    conn.commit()
    conn.close()

    return redirect(url_for('proveedores'))

@app.route('/eliminar_proveedor/<int:id>', methods=['POST'])
def eliminar_proveedor(id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM proveedores WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('proveedores'))

# Agregar presupuesto
@app.route('/agregar_presupuesto', methods=['GET', 'POST'])
def agregar_presupuesto():
    conn = obtener_conexion()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM centros_costos')
        centros_costos = cursor.fetchall()
        conn.close()
        return render_template('agregar_presupuesto.html', centros_costos=centros_costos)

    proveedor_nombre = request.form.get('proveedor_nombre')
    producto_nombre = request.form.get('producto_nombre')
    precio = request.form.get('precio')
    fecha = request.form.get('fecha')
    centro_costo_id = request.form.get('centro_costo_id')  # ✅ Recibir el ID correcto

    pdf = request.files.get('pdf')
    pdf_path = None
    if pdf and pdf.filename:
        import uuid
        pdf_filename = f"{uuid.uuid4().hex}_{pdf.filename}"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf.save(pdf_path)



    # Validar existencia de proveedor y producto
    cursor.execute('SELECT id FROM proveedores WHERE nombre = ?', (proveedor_nombre,))
    proveedor = cursor.fetchone()
    if not proveedor:
        conn.close()
        return "Error: El proveedor no existe.", 400
    proveedor_id = proveedor['id']

    cursor.execute('SELECT id FROM productos WHERE nombre = ?', (producto_nombre,))
    producto = cursor.fetchone()
    if not producto:
        cursor.execute('INSERT INTO productos (nombre, categoria, cantidad) VALUES (?, ?, ?)',
                       (producto_nombre, '', 0))
        producto_id = cursor.lastrowid
    else:
        producto_id = producto['id']

    # Insertar presupuesto
    cursor.execute('''
        INSERT INTO proveedores_productos (proveedor_id, producto_id, precio, fecha, centro_costo_id, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (proveedor_id, producto_id, precio, fecha, centro_costo_id, pdf_path))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))

# Ejecutar la aplicación
if __name__ == '__main__':
    crear_tablas()
    insertar_centros_costos()
    app.run(debug=True)