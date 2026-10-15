import os
import sqlite3
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

def inicializar_bd():
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            porcentaje REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio_compra REAL NOT NULL,
            precio_venta REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            total REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

inicializar_bd()

@app.route("/")
def index():
    return render_template("index.html")

# --- CATEGORÍAS ---
@app.route("/categorias", methods=["GET", "POST"])
def categorias():
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()
    
    if request.method == "POST":
        nombre = request.form.get("nombre").strip()
        porcentaje = request.form.get("porcentaje").strip()
        if nombre and porcentaje:
            try:
                cursor.execute("INSERT INTO categorias (nombre, porcentaje) VALUES (?, ?)", (nombre, float(porcentaje)))
                conn.commit()
            except sqlite3.IntegrityError:
                pass
        return redirect(url_for("categorias"))

    cursor.execute("SELECT id, nombre, porcentaje FROM categorias")
    cats = cursor.fetchall()
    conn.close()
    return render_template("categorias.html", categorias=cats)

@app.route("/editar_categoria", methods=["GET", "POST"])
def editar_categoria():
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()
    
    if request.method == "POST":
        cat_id = request.form.get("id")
        nombre = request.form.get("nombre").strip()
        porcentaje = request.form.get("porcentaje").strip()
        if nombre and porcentaje:
            cursor.execute("UPDATE categorias SET nombre = ?, porcentaje = ? WHERE id = ?", (nombre, float(porcentaje), cat_id))
            conn.commit()
            conn.close()
            return redirect(url_for("categorias"))

    cat_id = request.args.get("id")
    cursor.execute("SELECT id, nombre, porcentaje FROM categorias WHERE id = ?", (cat_id,))
    cat = cursor.fetchone()
    conn.close()
    return render_template("editar_categoria.html", categoria=cat)

@app.route("/eliminar_categoria/<int:id>")
def eliminar_categoria(id):
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("categorias"))

# --- INVENTARIO ---
@app.route("/inventario", methods=["GET", "POST"])
def inventario():
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()

    if request.method == "POST":
        nombre = request.form.get("nombre").strip()
        categoria = request.form.get("categoria").strip()
        p_compra = request.form.get("precio_compra").strip()
        stock = request.form.get("stock").strip()

        if nombre and categoria and p_compra and stock:
            try:
                p_c = float(p_compra)
                cursor.execute("SELECT porcentaje FROM categorias WHERE nombre = ?", (categoria,))
                res = cursor.fetchone()
                if res:
                    porcentaje = res[0]
                    p_v = p_c + (p_c * (porcentaje / 100.0))
                    
                    cursor.execute("""
                        INSERT INTO productos (nombre, categoria, precio_compra, precio_venta, stock)
                        VALUES (?, ?, ?, ?, ?)
                    """, (nombre, categoria, p_c, p_v, int(stock)))
                    conn.commit()
            except ValueError:
                pass
        return redirect(url_for("inventario"))

    cursor.execute("SELECT id, nombre, categoria, precio_compra, precio_venta, stock FROM productos")
    prods = cursor.fetchall()
    
    cursor.execute("SELECT nombre, porcentaje FROM categorias")
    cats = cursor.fetchall()
    conn.close()
    
    return render_template("inventario.html", productos=prods, categorias=cats)

@app.route("/editar_producto", methods=["GET", "POST"])
def editar_producto():
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()
    
    if request.method == "POST":
        prod_id = request.form.get("id")
        nombre = request.form.get("nombre").strip()
        categoria = request.form.get("categoria").strip()
        p_compra = request.form.get("precio_compra").strip()
        stock = request.form.get("stock").strip()

        if nombre and categoria and p_compra and stock:
            try:
                p_c = float(p_compra)
                cursor.execute("SELECT porcentaje FROM categorias WHERE nombre = ?", (categoria,))
                res = cursor.fetchone()
                if res:
                    porcentaje = res[0]
                    p_v = p_c + (p_c * (porcentaje / 100.0))
                    
                    cursor.execute("""
                        UPDATE productos SET nombre = ?, categoria = ?, precio_compra = ?, precio_venta = ?, stock = ?
                        WHERE id = ?
                    """, (nombre, categoria, p_c, p_v, int(stock), prod_id))
                    conn.commit()
            except ValueError:
                pass
            conn.close()
            return redirect(url_for("inventario"))

    prod_id = request.args.get("id")
    cursor.execute("SELECT id, nombre, categoria, precio_compra, stock FROM productos WHERE id = ?", (prod_id,))
    prod = cursor.fetchone()
    cursor.execute("SELECT nombre, porcentaje FROM categorias")
    cats = cursor.fetchall()
    conn.close()
    return render_template("editar_inventario.html", producto=prod, categorias=cats)

@app.route("/eliminar_producto/<int:id>")
def eliminar_producto(id):
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("inventario"))

# --- VENTAS ---
@app.route("/ventas", methods=["GET", "POST"])
def ventas():
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()

    if request.method == "POST":
        producto_nombre = request.form.get("producto").strip()
        cantidad = request.form.get("cantidad").strip()

        if producto_nombre and cantidad:
            try:
                cant = int(cantidad)
                cursor.execute("SELECT id, precio_venta, stock FROM productos WHERE nombre = ?", (producto_nombre,))
                prod = cursor.fetchone()
                if prod and cant > 0 and cant <= prod[2]:
                    prod_id, p_venta, stock_actual = prod[0], prod[1], prod[2]
                    total = p_venta * cant
                    nuevo_stock = stock_actual - cant

                    cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, prod_id))
                    cursor.execute("INSERT INTO ventas (producto, cantidad, total) VALUES (?, ?, ?)", (producto_nombre, cant, total))
                    conn.commit()
            except ValueError:
                pass
        return redirect(url_for("ventas"))

    cursor.execute("SELECT id, producto, cantidad, total, fecha FROM ventas")
    historial_ventas = cursor.fetchall()

    # Traer todos los productos para asegurar que aparezcan (incluso si el filtro daba problemas)
    cursor.execute("SELECT nombre FROM productos")
    productos_disponibles = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template("ventas.html", ventas=historial_ventas, productos_disponibles=productos_disponibles)

@app.route("/eliminar_venta/<int:id>")
def eliminar_venta(id):
    conn = sqlite3.connect("chucherias.db")
    cursor = conn.cursor()
    cursor.execute("SELECT producto, cantidad FROM ventas WHERE id = ?", (id,))
    v = cursor.fetchone()
    if v:
        prod_nombre, cant = v[0], v[1]
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE nombre = ?", (cant, prod_nombre))
        cursor.execute("DELETE FROM ventas WHERE id = ?", (id,))
        conn.commit()
    conn.close()
    return redirect(url_for("ventas"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)