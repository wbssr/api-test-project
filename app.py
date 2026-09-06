from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3
import hashlib
import secrets

app = FastAPI(title="电商测试系统 API", version="1.0")

security = HTTPBearer()

# ==================== 数据库初始化 ====================
DB_PATH = "test_api.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ==================== 数据模型 ====================
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ProductRequest(BaseModel):
    name: str
    price: float
    stock: int

class CartRequest(BaseModel):
    product_id: int
    quantity: int

class OrderRequest(BaseModel):
    pass  # 从购物车结算

# ==================== 工具函数 ====================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_hex(32)

def verify_token(token: str) -> Optional[int]:
    """验证 token，返回 user_id"""
    conn = get_db()
    result = conn.execute(
        "SELECT user_id FROM tokens WHERE token = ?", (token,)
    ).fetchone()
    conn.close()
    return result["user_id"] if result else None

# token 表
def init_token_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

init_token_table()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """从请求头获取当前用户"""
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="token 无效或已过期")
    return user_id

# ==================== 认证接口 ====================
@app.post("/register", tags=["认证"])
def register(req: RegisterRequest):
    conn = get_db()
    # 检查邮箱是否已注册
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    if len(req.password) < 6:
        conn.close()
        raise HTTPException(status_code=400, detail="密码长度至少 6 位")

    conn.execute(
        "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
        (req.email, hash_password(req.password), req.name)
    )
    conn.commit()
    conn.close()
    return {"message": "注册成功"}

@app.post("/login", tags=["认证"])
def login(req: LoginRequest):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
        (req.email, hash_password(req.password))
    ).fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    token = generate_token()
    conn = get_db()
    conn.execute("INSERT INTO tokens (token, user_id) VALUES (?, ?)", (token, user["id"]))
    conn.commit()
    conn.close()

    return {"token": token, "user_id": user["id"], "name": user["name"]}

# ==================== 商品接口 ====================
@app.get("/products", tags=["商品"])
def get_products():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return [dict(p) for p in products]

@app.get("/products/{product_id}", tags=["商品"])
def get_product(product_id: int):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return dict(product)

@app.post("/products", tags=["商品"])
def create_product(req: ProductRequest, user_id: int = Depends(get_current_user)):
    if req.price <= 0:
        raise HTTPException(status_code=400, detail="价格必须大于 0")
    if req.stock < 0:
        raise HTTPException(status_code=400, detail="库存不能为负")

    conn = get_db()
    conn.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        (req.name, req.price, req.stock)
    )
    conn.commit()
    conn.close()
    return {"message": "商品创建成功"}

@app.put("/products/{product_id}", tags=["商品"])
def update_product(product_id: int, req: ProductRequest, user_id: int = Depends(get_current_user)):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        raise HTTPException(status_code=404, detail="商品不存在")
    conn.execute(
        "UPDATE products SET name = ?, price = ?, stock = ? WHERE id = ?",
        (req.name, req.price, req.stock, product_id)
    )
    conn.commit()
    conn.close()
    return {"message": "商品更新成功"}

@app.delete("/products/{product_id}", tags=["商品"])
def delete_product(product_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        raise HTTPException(status_code=404, detail="商品不存在")
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"message": "商品删除成功"}

# ==================== 购物车接口 ====================
@app.post("/cart", tags=["购物车"])
def add_to_cart(req: CartRequest, user_id: int = Depends(get_current_user)):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (req.product_id,)).fetchone()
    if not product:
        conn.close()
        raise HTTPException(status_code=404, detail="商品不存在")
    if req.quantity <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="数量必须大于 0")
    conn.execute(
        "INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
        (user_id, req.product_id, req.quantity)
    )
    conn.commit()
    conn.close()
    return {"message": "已加入购物车"}

@app.get("/cart", tags=["购物车"])
def get_cart(user_id: int = Depends(get_current_user)):
    conn = get_db()
    items = conn.execute(
        """SELECT c.id, c.product_id, c.quantity, p.name, p.price
           FROM carts c JOIN products p ON c.product_id = p.id
           WHERE c.user_id = ?""", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(i) for i in items]

@app.delete("/cart/{cart_id}", tags=["购物车"])
def remove_from_cart(cart_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    item = conn.execute("SELECT * FROM carts WHERE id = ? AND user_id = ?", (cart_id, user_id)).fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="购物车项不存在")
    conn.execute("DELETE FROM carts WHERE id = ?", (cart_id,))
    conn.commit()
    conn.close()
    return {"message": "已移出购物车"}

# ==================== 订单接口 ====================
@app.post("/orders", tags=["订单"])
def create_order(user_id: int = Depends(get_current_user)):
    conn = get_db()
    cart_items = conn.execute(
        """SELECT c.product_id, c.quantity, p.price, p.stock, p.name
           FROM carts c JOIN products p ON c.product_id = p.id
           WHERE c.user_id = ?""", (user_id,)
    ).fetchall()

    if not cart_items:
        conn.close()
        raise HTTPException(status_code=400, detail="购物车为空")

    total = 0
    for item in cart_items:
        if item["quantity"] > item["stock"]:
            conn.close()
            raise HTTPException(status_code=400, detail=f"商品 {item['name']} 库存不足")
        total += item["quantity"] * item["price"]

    conn.execute("INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, 'pending')", (user_id, total))
    order_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    for item in cart_items:
        conn.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
            (order_id, item["product_id"], item["quantity"], item["price"])
        )
        conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (item["quantity"], item["product_id"])
        )

    conn.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"order_id": order_id, "total_amount": total, "status": "pending"}

@app.get("/orders", tags=["订单"])
def get_orders(user_id: int = Depends(get_current_user)):
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return [dict(o) for o in orders]

@app.post("/orders/{order_id}/cancel", tags=["订单"])
def cancel_order(order_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id)).fetchone()
    if not order:
        conn.close()
        raise HTTPException(status_code=404, detail="订单不存在")
    if order["status"] == "cancelled":
        conn.close()
        raise HTTPException(status_code=400, detail="订单已取消")

    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    for item in items:
        conn.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (item["quantity"], item["product_id"])
        )
    conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return {"message": "订单已取消"}