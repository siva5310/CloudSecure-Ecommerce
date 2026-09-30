
import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g, abort

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "store.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cloudsecure-dev-secret-change-in-production")

PRODUCT_SEED = [
    ("CloudBook Pro 14", "Laptops", 64999, 72999, "💻", "14-inch performance laptop for developers, students and professionals.", 4.8, 18),
    ("CloudBook Air 13", "Laptops", 52999, 59999, "🧑‍💻", "Slim everyday laptop with long battery life and a clean design.", 4.6, 14),
    ("Vision 4K Monitor", "Monitors", 24999, 29999, "🖥️", "Crisp 4K monitor for coding, content and productive work.", 4.7, 11),
    ("Pro Mechanical Keyboard", "Accessories", 2899, 3599, "⌨️", "Tactile mechanical keyboard with a comfortable productivity layout.", 4.8, 32),
    ("Silent Wireless Mouse", "Accessories", 1499, 1999, "🖱️", "Quiet wireless mouse with accurate tracking and ergonomic shape.", 4.5, 46),
    ("USB-C Dock Pro", "Accessories", 3999, 4999, "🔌", "Multi-port USB-C dock for modern laptops and workstations.", 4.4, 28),
    ("AirBeat Headphones", "Audio", 4999, 6499, "🎧", "Wireless headphones with clear audio and all-day comfort.", 4.7, 25),
    ("Pocket Speaker Mini", "Audio", 2299, 2999, "🔊", "Compact Bluetooth speaker for desk and travel.", 4.5, 37),
    ("Smart Watch X2", "Wearables", 3299, 4499, "⌚", "Smart everyday watch with activity tracking and notifications.", 4.6, 21),
    ("CloudFit Band", "Wearables", 1799, 2299, "⌁", "Lightweight fitness band with a bright display and health metrics.", 4.3, 40),
    ("Tech Backpack 20L", "Lifestyle", 1799, 2299, "🎒", "Water-resistant backpack with dedicated laptop protection.", 4.6, 34),
    ("Desk Lamp Pro", "Lifestyle", 1499, 1999, "💡", "Minimal adjustable LED lamp for focused desk work.", 4.4, 29),
]

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    conn = g.pop("db", None)
    if conn:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            old_price INTEGER NOT NULL,
            emoji TEXT NOT NULL,
            description TEXT NOT NULL,
            rating REAL NOT NULL,
            stock INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            pincode TEXT NOT NULL,
            total INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL
        );
    """)
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        conn.executemany(
            """INSERT INTO products
            (name, category, price, old_price, emoji, description, rating, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            PRODUCT_SEED,
        )
    conn.commit()
    conn.close()

def get_product(product_id):
    return db().execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

def get_cart():
    return session.get("cart", {})

def cart_details():
    cart = get_cart()
    items = []
    total = 0
    count = 0
    for pid, qty in cart.items():
        product = get_product(int(pid))
        if product:
            qty = int(qty)
            subtotal = product["price"] * qty
            items.append({"product": product, "qty": qty, "subtotal": subtotal})
            total += subtotal
            count += qty
    return items, total, count

@app.context_processor
def global_values():
    _, total, count = cart_details()
    return {"cart_count": count, "cart_total": total}

@app.template_filter("money")
def money(value):
    return f"₹{int(value):,}"

@app.route("/")
def home():
    products = db().execute(
        "SELECT * FROM products ORDER BY rating DESC, id LIMIT 8"
    ).fetchall()
    categories = db().execute(
        "SELECT category, COUNT(*) count FROM products GROUP BY category ORDER BY category"
    ).fetchall()
    return render_template("home.html", products=products, categories=categories)

@app.route("/shop")
def shop():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "featured")

    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND category=?"
        params.append(category)

    order_map = {
        "price_low": "price ASC",
        "price_high": "price DESC",
        "rating": "rating DESC",
        "featured": "rating DESC, id ASC",
    }
    sql += " ORDER BY " + order_map.get(sort, order_map["featured"])

    products = db().execute(sql, params).fetchall()
    categories = db().execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    return render_template(
        "shop.html",
        products=products,
        categories=categories,
        q=q,
        category=category,
        sort=sort,
    )

@app.route("/product/<int:product_id>")
def product(product_id):
    item = get_product(product_id)
    if not item:
        abort(404)
    related = db().execute(
        "SELECT * FROM products WHERE category=? AND id!=? LIMIT 4",
        (item["category"], product_id),
    ).fetchall()
    return render_template("product.html", product=item, related=related)

@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = get_product(product_id)
    if not product:
        abort(404)
    cart = dict(get_cart())
    key = str(product_id)
    current = int(cart.get(key, 0))
    if current < product["stock"]:
        cart[key] = current + 1
    session["cart"] = cart
    return redirect(request.referrer or url_for("shop"))

@app.post("/cart/update/<int:product_id>")
def update_cart(product_id):
    product = get_product(product_id)
    if not product:
        abort(404)
    qty = max(0, int(request.form.get("qty", 1)))
    qty = min(qty, product["stock"])
    cart = dict(get_cart())
    if qty == 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = qty
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.post("/cart/remove/<int:product_id>")
def remove_cart(product_id):
    cart = dict(get_cart())
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    items, total, _ = cart_details()
    return render_template("cart.html", items=items, total=total)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total, _ = cart_details()
    if not items:
        return redirect(url_for("shop"))
    if request.method == "POST":
        fields = ["name", "email", "phone", "address", "city", "pincode"]
        data = {f: request.form.get(f, "").strip() for f in fields}
        if not all(data.values()):
            return render_template("checkout.html", items=items, total=total, error="Please fill all required fields.")
        order_id = "CS-" + uuid.uuid4().hex[:8].upper()
        now = datetime.now().strftime("%d %b %Y, %I:%M %p")
        conn = db()
        conn.execute(
            """INSERT INTO orders
            (id, customer_name, email, phone, address, city, pincode, total, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, data["name"], data["email"], data["phone"], data["address"],
             data["city"], data["pincode"], total, now),
        )
        for item in items:
            p = item["product"]
            conn.execute(
                """INSERT INTO order_items
                (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)""",
                (order_id, p["id"], p["name"], item["qty"], p["price"]),
            )
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id=?",
                (item["qty"], p["id"]),
            )
        conn.commit()
        session["cart"] = {}
        return redirect(url_for("order_success", order_id=order_id))
    return render_template("checkout.html", items=items, total=total, error=None)

@app.route("/order-success/<order_id>")
def order_success(order_id):
    order = db().execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        abort(404)
    items = db().execute(
        "SELECT * FROM order_items WHERE order_id=?", (order_id,)
    ).fetchall()
    return render_template("success.html", order=order, items=items)

@app.get("/api/health")
def health():
    try:
        db().execute("SELECT 1").fetchone()
        return jsonify({
            "service": "CloudSecure E-Commerce",
            "status": "healthy",
            "database": "connected"
        })
    except Exception:
        return jsonify({
            "service": "CloudSecure E-Commerce",
            "status": "unhealthy"
        }), 503

@app.get("/api/products")
def api_products():
    rows = db().execute("SELECT id,name,category,price,rating,stock FROM products").fetchall()
    return jsonify([dict(row) for row in rows])

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)
