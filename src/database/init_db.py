"""
Initialisation de la base de données
AutoStockCheck - ECU Worldwide
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/database/autostockcheck.db')

def init_database():
    """Initialise toutes les tables"""
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT,
            storage_type TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des entreprises
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            company_name TEXT NOT NULL,
            storage_type TEXT,
            email_stock_manager TEXT,
            email_notification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Table des commandes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_reference TEXT NOT NULL,
            product_name TEXT,
            quantity_ordered INTEGER,
            quantity_stock INTEGER,
            price REAL,
            prediction INTEGER,
            probability REAL,
            status TEXT,
            client_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Table des emails
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            direction TEXT,
            recipient TEXT,
            subject TEXT,
            content TEXT,
            status TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')
    
    # Table des contacts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des livraisons (agenda)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            delivery_date TEXT NOT NULL,
            delivery_time TEXT,
            description TEXT,
            facture_name TEXT,
            facture_data TEXT,
            facture_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Table du stock
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT NOT NULL,
            reference TEXT,
            quantity INTEGER,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Table des utilisateurs (gestion des accès)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            user_id INTEGER,
            permissions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Base de données initialisée: {DB_PATH}")

def get_db():
    """Connexion à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hashage du mot de passe"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def create_default_admin():
    """Crée un administrateur par défaut"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Vérifier si un admin existe déjà
    cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    if not cursor.fetchone():
        # Créer l'admin par défaut
        hashed = hash_password("admin123")
        cursor.execute('''
            INSERT INTO users (username, password, email, company, storage_type, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', hashed, 'admin@autostockcheck.com', 'ECU Worldwide', 'entrepôt', 'admin'))
        
        user_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO companies (user_id, company_name, storage_type, email_stock_manager, email_notification)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'ECU Worldwide', 'entrepôt', 'stock@ecu-worldwide.com', 'notifications@ecu-worldwide.com'))
        
        conn.commit()
        print("✅ Administrateur par défaut créé (username: admin, password: admin123)")
    
    conn.close()

if __name__ == "__main__":
    init_database()
    create_default_admin()