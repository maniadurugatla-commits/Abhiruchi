import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# DB lives OUTSIDE the project root in production — set DB_PATH in .env
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'sithara.db'))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name  TEXT NOT NULL,
            phone      TEXT NOT NULL,
            date       TEXT NOT NULL,
            time       TEXT NOT NULL,
            guests     TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name  TEXT NOT NULL,
            phone      TEXT NOT NULL,
            address    TEXT NOT NULL,
            items      TEXT NOT NULL,
            status     TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            price       REAL    NOT NULL,
            description TEXT,
            image_path  TEXT,
            category    TEXT    DEFAULT 'main',
            is_active   INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name  TEXT NOT NULL,
            email      TEXT NOT NULL,
            message    TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        sample_items = [
            ('Dum Biryani Royale', 480.00, 'Slow-cooked basmati with saffron, whole spices & tender meat.',    'images/biryani.jpg',     'main'),
            ('Paneer Tikka',       220.00, 'Marinated paneer grilled in tandoor with spices.',                  'images/paneer.jpg',      'starter'),
            ('Mutton Biryani',     380.00, 'Hand-minced lamb charred over live coals with mint chutney.',       'images/mutton.avif',     'main'),
            ('Dal Makhani',        260.00, 'Black lentils slow-simmered overnight in tomato and cream.',        'images/dal makhni.jpg',  'main'),
            ('Chicken Curry',      520.00, 'Kashmiri slow-braised chicken in aromatic whole spices.',           'images/chicken.jpg',     'main'),
            ('Fish Fry',           180.00, 'Crispy golden fish fry with house spice blend and chutney.',        'images/fishfry.jpg',     'starter'),
            ('Chicken Kabob',      140.00, 'Juicy chicken skewers grilled over live coals.',                    'images/kabob.jpg',       'starter'),
            ('Veg Biryani',        120.00, 'Fragrant basmati rice with fresh seasonal vegetables.',             'images/veg biryani.jpg', 'main'),
        ]
        cursor.executemany(
            "INSERT INTO menu (name, price, description, image_path, category) VALUES (?, ?, ?, ?, ?)",
            sample_items
        )

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")
