import sqlite3
from config import DATABASE_PATH

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gifts (
            gift_id TEXT PRIMARY KEY,
            original_price INTEGER NOT NULL,
            in_stock BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gift_id TEXT NOT NULL,
            recipient_id INTEGER,
            anonymous BOOLEAN,
            comment_type TEXT,
            custom_comment TEXT,
            final_price INTEGER NOT NULL,
            stars_spent INTEGER NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            payment_payload TEXT UNIQUE,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (gift_id) REFERENCES gifts(gift_id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pending_purchases (
            payload TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            gift_id TEXT NOT NULL,
            recipient_id INTEGER NOT NULL,
            anonymous BOOLEAN NOT NULL,
            comment_type TEXT NOT NULL,
            custom_comment TEXT,
            final_price INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name)
    )
    conn.commit()
    conn.close()

def get_gift(gift_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT gift_id, original_price, in_stock FROM gifts WHERE gift_id = ?", (gift_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_all_gifts():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT gift_id, original_price, in_stock FROM gifts ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_gift(gift_id, original_price, in_stock=True):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO gifts (gift_id, original_price, in_stock) VALUES (?, ?, ?)",
        (gift_id, original_price, in_stock)
    )
    conn.commit()
    conn.close()

def delete_gift(gift_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM gifts WHERE gift_id = ?", (gift_id,))
    conn.commit()
    conn.close()

def update_gift_stock(gift_id, in_stock):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE gifts SET in_stock = ? WHERE gift_id = ?", (in_stock, gift_id))
    conn.commit()
    conn.close()

def add_purchase(user_id, gift_id, recipient_id, anonymous, comment_type, custom_comment, final_price, stars_spent, payload):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO purchases 
        (user_id, gift_id, recipient_id, anonymous, comment_type, custom_comment, final_price, stars_spent, payment_payload)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, gift_id, recipient_id, anonymous, comment_type, custom_comment, final_price, stars_spent, payload))
    conn.commit()
    purchase_id = cur.lastrowid
    conn.close()
    return purchase_id

def get_user_purchases(user_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT gift_id, recipient_id, anonymous, comment_type, custom_comment, final_price, purchase_date
        FROM purchases
        WHERE user_id = ?
        ORDER BY purchase_date DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM purchases")
    total_purchases = cur.fetchone()[0]
    cur.execute("SELECT SUM(stars_spent) FROM purchases")
    total_stars = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM purchases")
    total_buyers = cur.fetchone()[0]
    conn.close()
    return total_purchases, total_stars, total_buyers

def add_pending_purchase(payload, user_id, gift_id, recipient_id, anonymous, comment_type, custom_comment, final_price):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pending_purchases 
        (payload, user_id, gift_id, recipient_id, anonymous, comment_type, custom_comment, final_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (payload, user_id, gift_id, recipient_id, anonymous, comment_type, custom_comment, final_price))
    conn.commit()
    conn.close()

def get_pending_purchase(payload):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM pending_purchases WHERE payload = ?", (payload,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        class PendingPurchase:
            def __init__(self, row):
                self.payload = row[0]
                self.user_id = row[1]
                self.gift_id = row[2]
                self.recipient_id = row[3]
                self.anonymous = bool(row[4])
                self.comment_type = row[5]
                self.custom_comment = row[6]
                self.final_price = row[7]
                self.created_at = row[8]
        return PendingPurchase(row)
    return None

def delete_pending_purchase(payload):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM pending_purchases WHERE payload = ?", (payload,))
    conn.commit()
    conn.close()