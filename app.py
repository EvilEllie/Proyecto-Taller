# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
import pymysql.cursors
from config import Config
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

app = Flask(__name__)
app.config.from_object(Config)

def get_db():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config['MYSQL_PORT'],
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

    # Categorías para el modal del reporte
    cur.execute("SELECT * FROM categorias ORDER BY nombre_categoria")
    categorias = cur.fetchall()
    
    cur.close()
    
    return render_template('dashboard.html',
        total_piezas=total_piezas,
        stock_bajo=stock_bajo,
        total_movimientos=total_movimientos,
        alertas=alertas,
        ultimos_movimientos=ultimos_movimientos,
        categorias=categorias
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
               p.id_categoria, p.id_tipo,
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
    cur.execute("SELECT COUNT(*) AS total FROM piezas WHERE nombre_pieza = %s AND año = %s", (nombre, anio))
    if cur.fetchone()['total'] > 0:
        flash('Ya existe una pieza con ese nombre y año.', 'error')
        cur.close()
        return redirect(url_for('inventario'))
    usuario_registro = session.get('usuario', 'Sistema')
    cur.execute("""
        INSERT INTO piezas(nombre_pieza, año, cantidad, descripcion, id_categoria, id_tipo, fecha_registro, usuario_registro)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
    """, (nombre, anio, cantidad, descripcion, categoria, tipo, usuario_registro))
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
    forzar = request.form.get('forzar', 'no')
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM movimientos WHERE id_pieza = %s", (id,))
    resultado = cur.fetchone()
    if resultado['total'] > 0 and forzar != 'si':
        flash(f'piezaconmovimientos:{id}', 'error')
    else:
        cur.execute("DELETE FROM movimientos WHERE id_pieza = %s", (id,))
        cur.execute("DELETE FROM piezas WHERE id_pieza = %s", (id,))
        con.commit()
        flash('Pieza y sus movimientos eliminados.', 'success')
    cur.close()
    con.close()
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
    proveedor = request.form['proveedor']
    
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
        INSERT INTO movimientos (id_pieza, tipo_movimiento, cantidad, fecha, proveedor, usuario_registro)
        VALUES (%s, %s, %s, NOW(), %s, %s)
    """, (id_pieza, tipo, cantidad, proveedor, session.get('usuario', 'Sistema')))

    if tipo == 'ENTRADA':
        cur.execute("UPDATE piezas SET cantidad = cantidad + %s WHERE id_pieza = %s", (cantidad, id_pieza))
    elif tipo == 'SALIDA':
        cur.execute("UPDATE piezas SET cantidad = cantidad - %s WHERE id_pieza = %s", (cantidad, id_pieza))

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
    cur.execute("SELECT COUNT(*) AS total FROM categorias WHERE nombre_categoria = %s", (nombre,))
    if cur.fetchone()['total'] > 0:
        flash('Ya existe esa categoría.', 'error')
        cur.close()
        return redirect(url_for('inventario'))
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
# TIPOS
# ─────────────────────────────────────────
@app.route('/tipos/agregar', methods=['POST'])
@admin_required
def agregar_tipo():
    nombre = request.form['nombre_tipo']
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM tipo WHERE nombre_tipo = %s", (nombre,))
    if cur.fetchone()['total'] > 0:
        flash('Ya existe ese tipo.', 'error')
        cur.close()
        return redirect(url_for('inventario'))
    cur.execute("INSERT INTO tipo(nombre_tipo) VALUES(%s)", (nombre,))
    con.commit()
    cur.close()
    flash('Tipo agregado correctamente.', 'success')
    return redirect(url_for('inventario'))

@app.route('/tipos/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_tipo(id):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM piezas WHERE id_tipo = %s", (id,))
    if cur.fetchone()['total'] > 0:
        flash('No puedes eliminar un tipo que tiene piezas asignadas.', 'error')
    else:
        cur.execute("DELETE FROM tipo WHERE id_tipo = %s", (id,))
        con.commit()
        flash('Tipo eliminado.', 'success')
    cur.close()
    return redirect(url_for('inventario'))


# ─────────────────────────────────────────
# REPORTE PDF CON FILTROS
# ─────────────────────────────────────────
@app.route('/reporte/inventario')
@login_required
def reporte_inventario():
    # ── Leer filtros del query string ──
    fecha_inicio   = request.args.get('fecha_inicio', '').strip()
    fecha_fin      = request.args.get('fecha_fin', '').strip()
    nombre_pieza   = request.args.get('nombre_pieza', '').strip()
    id_categoria   = request.args.get('id_categoria', '').strip()
    tipo_movimiento = request.args.get('tipo_movimiento', '').strip()
    estado_stock   = request.args.get('estado_stock', '').strip()

    con = get_db()
    cur = con.cursor()

    # ── Movimientos con filtros (se ejecuta primero) ──
    query_movs = """
        SELECT m.fecha, m.tipo_movimiento, m.cantidad, m.proveedor,
               m.usuario_registro, p.nombre_pieza, p.id_pieza
        FROM movimientos m
        JOIN piezas p ON m.id_pieza = p.id_pieza
        WHERE 1=1
    """
    params_movs = []

    if fecha_inicio:
        query_movs += " AND DATE(m.fecha) >= %s"
        params_movs.append(fecha_inicio)
    if fecha_fin:
        query_movs += " AND DATE(m.fecha) <= %s"
        params_movs.append(fecha_fin)
    if nombre_pieza:
        query_movs += " AND p.nombre_pieza LIKE %s"
        params_movs.append(f"%{nombre_pieza}%")
    if id_categoria:
        query_movs += " AND p.id_categoria = %s"
        params_movs.append(id_categoria)
    if tipo_movimiento:
        query_movs += " AND m.tipo_movimiento = %s"
        params_movs.append(tipo_movimiento)

    query_movs += " ORDER BY m.fecha DESC"
    cur.execute(query_movs, params_movs)
    movimientos = cur.fetchall()

    # ── Piezas: solo las que tienen movimientos en el rango de fechas ──
    ids_piezas_con_movs = list({m['id_pieza'] for m in movimientos})

    if not ids_piezas_con_movs:
        piezas = []
    else:
        placeholders = ','.join(['%s'] * len(ids_piezas_con_movs))
        query_piezas = f"""
            SELECT p.nombre_pieza, p.año, p.cantidad, p.descripcion,
                   p.fecha_registro, p.usuario_registro,
                   c.nombre_categoria, t.nombre_tipo,
                   CASE WHEN p.cantidad <= 5 THEN 'STOCK BAJO' ELSE 'STOCK NORMAL' END AS estado
            FROM piezas p
            JOIN categorias c ON p.id_categoria = c.id_categoria
            JOIN tipo t ON p.id_tipo = t.id_tipo
            WHERE p.id_pieza IN ({placeholders})
        """
        params_piezas = ids_piezas_con_movs[:]

        if estado_stock == 'bajo':
            query_piezas += " AND p.cantidad <= 5"
        elif estado_stock == 'normal':
            query_piezas += " AND p.cantidad > 5"

        query_piezas += " ORDER BY p.nombre_pieza ASC"
        cur.execute(query_piezas, params_piezas)
        piezas = cur.fetchall()

    # Nombre de categoría para el encabezado
    nombre_categoria_filtro = ''
    if id_categoria:
        cur.execute("SELECT nombre_categoria FROM categorias WHERE id_categoria = %s", (id_categoria,))
        cat = cur.fetchone()
        if cat:
            nombre_categoria_filtro = cat['nombre_categoria']

    cur.close()

    if len(piezas) == 0 and len(movimientos) == 0:
        flash('No se encontraron datos con los filtros seleccionados.', 'error')
        return redirect(url_for('dashboard'))

    # ── Construir resumen de filtros aplicados ──
    filtros_aplicados = []
    if fecha_inicio:
        filtros_aplicados.append(f"Desde: {fecha_inicio}")
    if fecha_fin:
        filtros_aplicados.append(f"Hasta: {fecha_fin}")
    if nombre_pieza:
        filtros_aplicados.append(f"Pieza: {nombre_pieza}")
    if nombre_categoria_filtro:
        filtros_aplicados.append(f"Categoría: {nombre_categoria_filtro}")
    if tipo_movimiento:
        filtros_aplicados.append(f"Movimiento: {tipo_movimiento}")
    if estado_stock:
        filtros_aplicados.append(f"Stock: {'Bajo' if estado_stock == 'bajo' else 'Normal'}")
    texto_filtros = "  |  ".join(filtros_aplicados) if filtros_aplicados else "Sin filtros aplicados (reporte completo)"

    # ── Generar PDF ──
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    elements.append(Paragraph("Rectificaciones Rio", styles['Title']))
    elements.append(Paragraph("Reporte de Inventario y Trazabilidad", styles['Heading2']))
    elements.append(Spacer(1, 6))

    # Filtros aplicados
    elements.append(Paragraph(
        f"<font size='8' color='grey'>Filtros: {texto_filtros}</font>",
        styles['Normal']
    ))
    elements.append(Spacer(1, 16))

    # ── Tabla inventario ──
    if piezas:
        elements.append(Paragraph("Inventario de Piezas", styles['Heading3']))
        elements.append(Spacer(1, 10))
        data = [['Pieza', 'Año', 'Cant.', 'Categoría', 'Tipo', 'Estado', 'Registrada', 'Por']]
        for p in piezas:
            fecha_reg = p['fecha_registro'].strftime('%d/%m/%Y') if p.get('fecha_registro') else 'N/A'
            data.append([
                p['nombre_pieza'], str(p['año']), str(p['cantidad']),
                p['nombre_categoria'], p['nombre_tipo'], p['estado'],
                fecha_reg, p.get('usuario_registro') or 'Sistema'
            ])

        table = Table(data, repeatRows=1, colWidths=[110, 35, 35, 75, 55, 65, 65, 55])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8B0000')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 30))

    # ── Tabla movimientos ──
    if movimientos:
        elements.append(Paragraph("Registro de Movimientos y Procedencia", styles['Heading3']))
        elements.append(Spacer(1, 10))
        data2 = [['Fecha', 'Pieza', 'Tipo', 'Cantidad', 'Proveedor', 'Registrado por']]
        for m in movimientos:
            fecha_str = m['fecha'].strftime('%d/%m/%Y %H:%M') if m['fecha'] else 'N/A'
            data2.append([
                fecha_str,
                m['nombre_pieza'],
                m['tipo_movimiento'],
                str(m['cantidad']),
                m['proveedor'] or 'N/A',
                m.get('usuario_registro') or 'Sistema'
            ])

        table2 = Table(data2, repeatRows=1, colWidths=[90, 110, 55, 45, 100, 90])
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8B0000')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(table2)

    doc.build(elements)
    buffer.seek(0)

    from flask import make_response
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_inventario.pdf'
    return response

# ─────────────────────────────────────────
# ARRANCAR
# ─────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
