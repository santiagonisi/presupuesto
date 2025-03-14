import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Configuración de la carpeta de subida
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Conectar a la base de datos
def obtener_conexion():
    conn = sqlite3.connect('empresa.db', check_same_thread=False)
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
    # Eliminar la tabla proveedores_productos si existe
    cursor.execute('DROP TABLE IF EXISTS proveedores_productos')
    # Crear la tabla proveedores_productos con la nueva estructura
    cursor.execute('''
    CREATE TABLE proveedores_productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        precio REAL NOT NULL,
        fecha TEXT,
        centro_costo_id INTEGER,
        pdf_path TEXT,
        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
        FOREIGN KEY (producto_id) REFERENCES productos(id),
        FOREIGN KEY (centro_costo_id) REFERENCES centros_costos(id)
    )
    ''')
    conn.commit()
    conn.close()

# Página principal
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

@app.route('/proveedores')
def proveedores():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM proveedores')
    proveedores = cursor.fetchall()
    conn.close()
    return render_template('proveedores.html', proveedores=proveedores)

@app.route('/agregar_proveedor', methods=['GET', 'POST'])
def agregar_proveedor():
    if request.method == 'POST':
        # Lógica para agregar un proveedor
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
    return render_template('agregar_proveedor.html')

@app.route('/eliminar_proveedor/<int:id>', methods=['POST'])
def eliminar_proveedor(id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM proveedores WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('proveedores'))

@app.route('/agregar_presupuesto', methods=['GET', 'POST'])
def agregar_presupuesto():
    if request.method == 'POST':
        proveedor_nombre = request.form['proveedor_nombre']
        producto_nombre = request.form['producto_nombre']
        precio = request.form['precio']
        fecha = request.form['fecha']
        centro_costo_id = request.form['centro_costo_id']
        pdf = request.files['pdf']

        # Guardar el PDF en el servidor
        pdf_filename = pdf.filename
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf.save(pdf_path)

        try:
            conn = obtener_conexion()
            cursor = conn.cursor()

            # Verificar si el proveedor existe
            cursor.execute('SELECT id FROM proveedores WHERE nombre = ?', (proveedor_nombre,))
            proveedor = cursor.fetchone()
            if not proveedor:
                cursor.execute('INSERT INTO proveedores (nombre, razonsocial, contacto, cuit, rubro, ubicacion) VALUES (?, ?, ?, ?, ?, ?)',
                               (proveedor_nombre, '', '', '', '', ''))
                proveedor_id = cursor.lastrowid
            else:
                proveedor_id = proveedor['id']

            # Verificar si el producto existe
            cursor.execute('SELECT id FROM productos WHERE nombre = ?', (producto_nombre,))
            producto = cursor.fetchone()
            if not producto:
                cursor.execute('INSERT INTO productos (nombre, categoria, cantidad) VALUES (?, ?, ?)',
                               (producto_nombre, '', 0))
                producto_id = cursor.lastrowid
            else:
                producto_id = producto['id']

            # Insertar el presupuesto
            cursor.execute('''
                INSERT INTO proveedores_productos (proveedor_id, producto_id, precio, fecha, centro_costo_id, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (proveedor_id, producto_id, precio, fecha, centro_costo_id, pdf_path))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error al insertar presupuesto: {e}")
        finally:
            conn.close()

        return redirect(url_for('index'))
    else:
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
    crear_tablas()
    app.run(debug=True)
