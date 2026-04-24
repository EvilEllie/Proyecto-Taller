# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
import pymysql.cursors
from config import Config
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

def get_db():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )
# ─────────────────────────────────────────
# DECORADOR: proteger rutas
# ─────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        if session.get('rol') != 'Administrador':
            flash('No tienes permisos para acceder a esa sección.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────
# LOGIN / LOGOUT
# ─────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s AND contrasena = %s", (usuario, contrasena))
        user = cur.fetchone()
        cur.close()
        
        if user:
            session['id_usuario'] = user['id_usuario']
            session['usuario'] = user['usuario']
            session['rol'] = user['rol']
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    con = get_db()
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) AS total FROM piezas")
    total_piezas = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) AS bajo FROM piezas WHERE cantidad <= 5")
    stock_bajo = cur.fetchone()['bajo']
    
    cur.execute("SELECT COUNT(*) AS total FROM movimientos")
    total_movimientos = cur.fetchone()['total']
    
    cur.execute("""
        SELECT p.nombre_pieza, p.cantidad,
        CASE WHEN p.cantidad <= 5 THEN 'STOCK BAJO' ELSE 'STOCK NORMAL' END AS estado
        FROM piezas p
        WHERE p.cantidad <= 5
        ORDER BY p.cantidad ASC
        LIMIT 5
    """)
    alertas = cur.fetchall()
    
    cur.execute("""
        SELECT m.tipo_movimiento, m.cantidad, m.fecha, p.nombre_pieza
        FROM movimientos m
        JOIN piezas p ON m.id_pieza = p.id_pieza
        ORDER BY m.fecha DESC
        LIMIT 5
    """)
    ultimos_movimientos = cur.fetchall()
    
    cur.close()
    
    return render_template('dashboard.html',
        total_piezas=total_piezas,
        stock_bajo=stock_bajo,
        total_movimientos=total_movimientos,
        alertas=alertas,
        ultimos_movimientos=ultimos_movimientos
    )

# ─────────────────────────────────────────
# INVENTARIO
# ─────────────────────────────────────────
@app.route('/inventario')
@login_required
def inventario():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT p.id_pieza, p.nombre_pieza, p.año, p.cantidad, p.descripcion,
               c.nombre_categoria, t.nombre_tipo,
               CASE WHEN p.cantidad <= 5 THEN 'STOCK BAJO' ELSE 'STOCK NORMAL' END AS estado_stock
        FROM piezas p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        JOIN tipo t ON p.id_tipo = t.id_tipo
        ORDER BY p.nombre_pieza ASC
    """)
    piezas = cur.fetchall()
    
    cur.execute("SELECT * FROM categorias")
    categorias = cur.fetchall()
    
    cur.execute("SELECT * FROM tipo")
    tipos = cur.fetchall()
    
    cur.close()
    return render_template('inventario.html', piezas=piezas, categorias=categorias, tipos=tipos)


@app.route('/inventario/agregar', methods=['POST'])
@login_required
def agregar_pieza():
    nombre = request.form['nombre_pieza']
    anio = request.form['año']
    cantidad = request.form['cantidad']
    descripcion = request.form['descripcion']
    categoria = request.form['id_categoria']
    tipo = request.form['id_tipo']
    
    con = get_db()
    cur = con.cursor()
    cur.execute("INSERT INTO piezas(nombre_pieza, año, cantidad, descripcion, id_categoria, id_tipo) VALUES (%s, %s, %s, %s, %s, %s)", (nombre, anio, cantidad, descripcion, categoria, tipo))
    con.commit()
    cur.close()
    
    flash('Pieza agregada correctamente.', 'success')
    return redirect(url_for('inventario'))


@app.route('/inventario/editar/<int:id>', methods=['POST'])
@login_required
def editar_pieza(id):
    nombre = request.form['nombre_pieza']
    anio = request.form['año']
    descripcion = request.form['descripcion']
    categoria = request.form['id_categoria']
    tipo = request.form['id_tipo']
    
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        UPDATE piezas SET nombre_pieza=%s, año=%s, descripcion=%s,
        id_categoria=%s, id_tipo=%s WHERE id_pieza=%s
    """, (nombre, anio, descripcion, categoria, tipo, id))
    con.commit()
    cur.close()
    
    flash('Pieza actualizada correctamente.', 'success')
    return redirect(url_for('inventario'))


@app.route('/inventario/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_pieza(id):
    con = get_db()
    cur = con.cursor()
    cur.execute("DELETE FROM piezas WHERE id_pieza = %s", (id,))
    con.commit()
    cur.close()
    flash('Pieza eliminada.', 'success')
    return redirect(url_for('inventario'))


# ─────────────────────────────────────────
# MOVIMIENTOS
# ─────────────────────────────────────────
@app.route('/movimientos')
@login_required
def movimientos():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT m.id_movimiento, p.nombre_pieza, m.tipo_movimiento, m.cantidad, m.fecha
        FROM movimientos m
        JOIN piezas p ON m.id_pieza = p.id_pieza
        ORDER BY m.fecha DESC
    """)
    movs = cur.fetchall()
    
    cur.execute("SELECT id_pieza, nombre_pieza FROM piezas ORDER BY nombre_pieza")
    piezas = cur.fetchall()
    
    cur.close()
    return render_template('movimientos.html', movimientos=movs, piezas=piezas)


@app.route('/movimientos/registrar', methods=['POST'])
@login_required
def registrar_movimiento():
    id_pieza = request.form['id_pieza']
    tipo = request.form['tipo_movimiento']
    cantidad = request.form['cantidad']
    
    con = get_db()
    cur = con.cursor()
    
    if tipo == 'SALIDA':
        cur.execute("SELECT cantidad FROM piezas WHERE id_pieza = %s", (id_pieza,))
        pieza = cur.fetchone()
        if pieza['cantidad'] < int(cantidad):
            flash('Stock insuficiente para registrar la salida.', 'error')
            cur.close()
            return redirect(url_for('movimientos'))
    
    cur.execute("""
        INSERT INTO movimientos (id_pieza, tipo_movimiento, cantidad, fecha)
        VALUES (%s, %s, %s, NOW())
    """, (id_pieza, tipo, cantidad))
    con.commit()
    cur.close()
    
    flash(f'Movimiento de {tipo} registrado correctamente.', 'success')
    return redirect(url_for('movimientos'))


# ─────────────────────────────────────────
# USUARIOS (solo Admin)
# ─────────────────────────────────────────
@app.route('/usuarios')
@admin_required
def usuarios():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM usuarios")
    users = cur.fetchall()
    cur.close()
    return render_template('usuarios.html', usuarios=users)


@app.route('/usuarios/agregar', methods=['POST'])
@admin_required
def agregar_usuario():
    usuario = request.form['usuario']
    contrasena = request.form['contrasena']
    rol = request.form['rol']
    
    con = get_db()
    cur = con.cursor()
    cur.execute("INSERT INTO usuarios(usuario, contrasena, rol) VALUES (%s, %s, %s)", (usuario, contrasena, rol))
    con.commit()
    cur.close()
    
    flash('Usuario creado correctamente.', 'success')
    return redirect(url_for('usuarios'))


@app.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_usuario(id):
    if id == session['id_usuario']:
        flash('No puedes eliminar tu propio usuario.', 'error')
        return redirect(url_for('usuarios'))
    
    con = get_db()
    cur = con.cursor()
    cur.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id,))
    con.commit()
    cur.close()
    
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('usuarios'))


# ─────────────────────────────────────────
# CATEGORIAS Y TIPOS
# ─────────────────────────────────────────
@app.route('/api/categorias')
@login_required
def api_categorias():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM categorias")
    data = cur.fetchall()
    cur.close()
    con.close()
    return jsonify(data)

@app.route('/categorias/agregar', methods=['POST'])
@admin_required
def agregar_categoria():
    nombre = request.form['nombre_categoria']
    con = get_db()
    cur = con.cursor()
    cur.execute("INSERT INTO categorias(nombre_categoria) VALUES(%s)", (nombre,))
    con.commit()
    cur.close()
    con.close()
    flash('Categoría agregada correctamente.', 'success')
    return redirect(url_for('inventario'))

@app.route('/categorias/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_categoria(id):
    con = get_db()
    cur = con.cursor()
    # Verificar que no haya piezas usando esta categoría
    cur.execute("SELECT COUNT(*) AS total FROM piezas WHERE id_categoria = %s", (id,))
    resultado = cur.fetchone()
    if resultado['total'] > 0:
        flash('No puedes eliminar una categoría que tiene piezas asignadas.', 'error')
    else:
        cur.execute("DELETE FROM categorias WHERE id_categoria = %s", (id,))
        con.commit()
        flash('Categoría eliminada.', 'success')
    cur.close()
    con.close()
    return redirect(url_for('inventario'))

# ─────────────────────────────────────────
# ARRANCAR
# ─────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
