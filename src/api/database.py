import sqlite3
import json
import hashlib
import re
import secrets
import string
from datetime import datetime, timedelta
from config import DB_PATH
from logger import log_action as log_audit

# ==================== FONCTIONS DE VALIDATION ====================

def validate_email(email):
    """Valide le format de l'email"""
    if not email:
        return False, "L'email est requis"
    
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False, "Format d'email invalide. Exemple: utilisateur@domaine.com"
    
    if len(email) > 255:
        return False, "L'email ne peut pas dépasser 255 caractères"
    
    return True, ""


def validate_password(password, is_new_user=True):
    """Valide le mot de passe"""
    if is_new_user and not password:
        return False, "Le mot de passe est requis"
    
    if password:
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"
        
        if len(password) > 128:
            return False, "Le mot de passe ne peut pas dépasser 128 caractères"
        
        if not re.search(r'[A-Z]', password):
            return False, "Le mot de passe doit contenir au moins une lettre majuscule"
        
        if not re.search(r'[a-z]', password):
            return False, "Le mot de passe doit contenir au moins une lettre minuscule"
        
        if not re.search(r'[0-9]', password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        
        special_chars = r'[!@#$%^&*(),.?":{}|<>]'
        if not re.search(special_chars, password):
            return False, "Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*...)"
    
    return True, ""


def generate_random_password(length=12):
    """Génère un mot de passe aléatoire sécurisé"""
    if length < 8:
        length = 8
    
    uppercase = secrets.choice(string.ascii_uppercase)
    lowercase = secrets.choice(string.ascii_lowercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")
    
    remaining_length = length - 4
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = ''.join(secrets.choice(all_chars) for _ in range(remaining_length))
    
    password_list = list(uppercase + lowercase + digit + special + remaining)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)


def validate_username(username):
    """Valide le nom d'utilisateur"""
    if not username:
        return False, "Le nom d'utilisateur est requis"
    
    if len(username) < 3:
        return False, "Le nom d'utilisateur doit contenir au moins 3 caractères"
    
    if len(username) > 50:
        return False, "Le nom d'utilisateur ne peut pas dépasser 50 caractères"
    
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return False, "Le nom d'utilisateur ne peut contenir que des lettres, chiffres, _, ., -"
    
    return True, ""


def validate_phone(phone):
    """Valide le numéro de téléphone"""
    if not phone:
        return True, ""
    
    phone_regex = r'^(\+[0-9]{1,3}[0-9]{4,14}|0[0-9]{9,14})$'
    if not re.match(phone_regex, phone):
        return False, "Format de téléphone invalide. Exemple: +212612345678 ou 0612345678"
    
    return True, ""


def is_email_unique(email, exclude_user_id=None):
    """Vérifie si l'email est unique"""
    conn = get_db()
    cursor = conn.cursor()
    if exclude_user_id:
        cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, exclude_user_id))
    else:
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return not exists


def is_username_unique(username, exclude_user_id=None):
    """Vérifie si le nom d'utilisateur est unique"""
    conn = get_db()
    cursor = conn.cursor()
    if exclude_user_id:
        cursor.execute('SELECT id FROM users WHERE username = ? AND id != ?', (username, exclude_user_id))
    else:
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    exists = cursor.fetchone() is not None
    conn.close()
    return not exists


# ==================== FONCTIONS BASE DE DONNÉES ====================

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def add_audit_log(user_id, user_name, user_role, action, details, ip_address, entity_type=None, entity_id=None):
    """Ajoute un log d'audit (version fichier)"""
    log_audit(user_id, user_name, user_role, action, details, ip_address, entity_type, entity_id)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # ==================== TABLE USERS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            company TEXT,
            role TEXT DEFAULT 'user',
            roles TEXT DEFAULT '["user"]',
            statut TEXT DEFAULT 'actif',
            avatar TEXT,
            telephone TEXT,
            fullname TEXT,
            sexe TEXT,
            nationalite TEXT,
            birthdate TEXT,
            adresse TEXT,
            hire_date TEXT,
            departement TEXT,
            cv_path TEXT,
            contrat_path TEXT,
            diplomes_path TEXT,
            autres_path TEXT,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Vérifier et ajouter les colonnes manquantes
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    colonnes_manquantes = {
        'avatar': "ALTER TABLE users ADD COLUMN avatar TEXT",
        'fullname': "ALTER TABLE users ADD COLUMN fullname TEXT",
        'sexe': "ALTER TABLE users ADD COLUMN sexe TEXT",
        'nationalite': "ALTER TABLE users ADD COLUMN nationalite TEXT",
        'birthdate': "ALTER TABLE users ADD COLUMN birthdate TEXT",
        'adresse': "ALTER TABLE users ADD COLUMN adresse TEXT",
        'hire_date': "ALTER TABLE users ADD COLUMN hire_date TEXT",
        'departement': "ALTER TABLE users ADD COLUMN departement TEXT",
        'cv_path': "ALTER TABLE users ADD COLUMN cv_path TEXT",
        'contrat_path': "ALTER TABLE users ADD COLUMN contrat_path TEXT",
        'diplomes_path': "ALTER TABLE users ADD COLUMN diplomes_path TEXT",
        'autres_path': "ALTER TABLE users ADD COLUMN autres_path TEXT"
    }

    for col, sql in colonnes_manquantes.items():
        if col not in columns:
            try:
                cursor.execute(sql)
                print(f"✅ Colonne {col} ajoutée")
            except:
                pass
    
    # ==================== TABLE STOCK_ITEMS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reference TEXT NOT NULL,
            nom TEXT NOT NULL,
            categorie TEXT DEFAULT 'Divers',
            quantite INTEGER DEFAULT 0,
            stock_min INTEGER DEFAULT 5,
            prix REAL DEFAULT 0,
            emplacement TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Ajouter colonnes manquantes à stock_items
    cursor.execute("PRAGMA table_info(stock_items)")
    stock_columns = [col[1] for col in cursor.fetchall()]
    
    stock_colonnes_manquantes = {
        'categorie': "ALTER TABLE stock_items ADD COLUMN categorie TEXT DEFAULT 'Divers'",
        'quantite': "ALTER TABLE stock_items ADD COLUMN quantite INTEGER DEFAULT 0",
        'stock_min': "ALTER TABLE stock_items ADD COLUMN stock_min INTEGER DEFAULT 5",
        'prix': "ALTER TABLE stock_items ADD COLUMN prix REAL DEFAULT 0",
        'emplacement': "ALTER TABLE stock_items ADD COLUMN emplacement TEXT"
    }
    
    for col, sql in stock_colonnes_manquantes.items():
        if col not in stock_columns:
            try:
                cursor.execute(sql)
                print(f"✅ Colonne {col} ajoutée à stock_items")
            except:
                pass
    
    # ==================== TABLE STOCK_MOUVEMENTS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_mouvements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER,
            reference TEXT,
            nom TEXT,
            type TEXT NOT NULL,
            quantite INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            commentaire TEXT,
            user_id INTEGER,
            FOREIGN KEY (produit_id) REFERENCES stock_items(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ==================== TABLE COMMANDES_RECUES (avec chemin_fichier) ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commandes_recues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            reference TEXT NOT NULL,
            client TEXT,
            fournisseur TEXT,
            produits TEXT,
            statut TEXT DEFAULT 'valide',
            date_reception DATE,
            user_id INTEGER,
            chemin_fichier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Ajouter colonne chemin_fichier si manquante
    cursor.execute("PRAGMA table_info(commandes_recues)")
    commandes_columns = [col[1] for col in cursor.fetchall()]
    if 'chemin_fichier' not in commandes_columns:
        try:
            cursor.execute("ALTER TABLE commandes_recues ADD COLUMN chemin_fichier TEXT")
            print("✅ Colonne chemin_fichier ajoutée à commandes_recues")
        except:
            pass
    
    # ==================== TABLE FACTURES_RECUES ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factures_recues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            reference_reception TEXT NOT NULL,
            informations TEXT,
            contenu TEXT,
            statut TEXT DEFAULT 'en-attente',
            chemin_fichier TEXT,
            user_id INTEGER,
            ajoute_par TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Ajouter colonnes manquantes à factures_recues
    cursor.execute("PRAGMA table_info(factures_recues)")
    factures_columns = [col[1] for col in cursor.fetchall()]
    
    factures_colonnes_manquantes = {
        'created_at': "ALTER TABLE factures_recues ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        'date_ajout': "ALTER TABLE factures_recues ADD COLUMN date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        'informations': "ALTER TABLE factures_recues ADD COLUMN informations TEXT",
        'ajoute_par': "ALTER TABLE factures_recues ADD COLUMN ajoute_par TEXT"
    }
    
    for col, sql in factures_colonnes_manquantes.items():
        if col not in factures_columns:
            try:
                cursor.execute(sql)
                print(f"✅ Colonne {col} ajoutée à factures_recues")
            except:
                pass
    
    # ==================== TABLE ANOMALIES ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facture_id INTEGER,
            reception_id INTEGER,
            produits TEXT,
            statut TEXT DEFAULT 'en_attente',
            date_correction TIMESTAMP,
            commentaire TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (facture_id) REFERENCES factures_recues(id),
            FOREIGN KEY (reception_id) REFERENCES commandes_recues(id)
        )
    ''')
    
    # ==================== TABLE CLIENTS_EXTERNES ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients_externes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT,
            telephone TEXT,
            adresse TEXT,
            dossier_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ==================== TABLE NOTIFICATIONS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            read INTEGER DEFAULT 0,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ==================== TABLE USER_SESSIONS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            ip_address TEXT,
            user_agent TEXT,
            login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP,
            logout_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Ajouter colonne logout_at si manquante
    cursor.execute("PRAGMA table_info(user_sessions)")
    sessions_columns = [col[1] for col in cursor.fetchall()]
    if 'logout_at' not in sessions_columns:
        try:
            cursor.execute("ALTER TABLE user_sessions ADD COLUMN logout_at TIMESTAMP")
            print("✅ Colonne logout_at ajoutée à user_sessions")
        except:
            pass
    
    # ==================== TABLE AUDIT_LOGS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            user_role TEXT,
            action TEXT,
            entity_type TEXT,
            entity_id TEXT,
            old_data TEXT,
            new_data TEXT,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Ajouter colonnes manquantes à audit_logs
    cursor.execute("PRAGMA table_info(audit_logs)")
    audit_columns = [col[1] for col in cursor.fetchall()]
    
    audit_colonnes_manquantes = {
        'user_name': "ALTER TABLE audit_logs ADD COLUMN user_name TEXT",
        'user_role': "ALTER TABLE audit_logs ADD COLUMN user_role TEXT",
        'old_data': "ALTER TABLE audit_logs ADD COLUMN old_data TEXT",
        'new_data': "ALTER TABLE audit_logs ADD COLUMN new_data TEXT",
        'user_agent': "ALTER TABLE audit_logs ADD COLUMN user_agent TEXT"
    }
    
    for col, sql in audit_colonnes_manquantes.items():
        if col not in audit_columns:
            try:
                cursor.execute(sql)
                print(f"✅ Colonne {col} ajoutée à audit_logs")
            except:
                pass
    
    # ==================== UTILISATEURS PAR DÉFAUT ====================
    
    # Admin
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        hashed = hash_password('Admin@123')
        cursor.execute('''
            INSERT INTO users (username, password, email, role, statut, fullname)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', hashed, 'admin@autostockcheck.com', 'admin', 'actif', 'Administrateur'))
        print("✅ Admin créé (admin/Admin@123)")
    
    # Responsable stock
    cursor.execute('SELECT id FROM users WHERE username = ?', ('stock_manager',))
    if not cursor.fetchone():
        hashed = hash_password('Stock@123')
        cursor.execute('''
            INSERT INTO users (username, password, email, role, statut, fullname, departement)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('stock_manager', hashed, 'stock@autostockcheck.com', 'stock', 'actif', 'Responsable Stock', 'stock'))
        print("✅ Responsable stock créé (stock_manager/Stock@123)")
    
    # Responsable qualité
    cursor.execute('SELECT id FROM users WHERE username = ?', ('qualite_manager',))
    if not cursor.fetchone():
        hashed = hash_password('Qualite@123')
        cursor.execute('''
            INSERT INTO users (username, password, email, role, statut, fullname, departement)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('qualite_manager', hashed, 'qualite@autostockcheck.com', 'qualite', 'actif', 'Responsable Qualité', 'qualite'))
        print("✅ Responsable qualité créé (qualite_manager/Qualite@123)")
    
    # Responsable réception
    cursor.execute('SELECT id FROM users WHERE username = ?', ('reception_manager',))
    if not cursor.fetchone():
        hashed = hash_password('Reception@123')
        cursor.execute('''
            INSERT INTO users (username, password, email, role, statut, fullname, departement)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('reception_manager', hashed, 'reception@autostockcheck.com', 'reception', 'actif', 'Responsable Réception', 'reception'))
        print("✅ Responsable réception créé (reception_manager/Reception@123)")
    
    # Utilisateur standard
    cursor.execute('SELECT id FROM users WHERE username = ?', ('user',))
    if not cursor.fetchone():
        hashed = hash_password('User@123')
        cursor.execute('''
            INSERT INTO users (username, password, email, role, statut, fullname)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('user', hashed, 'user@autostockcheck.com', 'user', 'actif', 'Utilisateur Standard'))
        print("✅ Utilisateur standard créé (user/User@123)")
    
    conn.commit()
    conn.close()
    print("=" * 50)
    print("✅ Base de données initialisée avec toutes les tables")
    print("📝 Comptes par défaut:")
    print("   - Admin: admin / Admin@123")
    print("   - Stock: stock_manager / Stock@123")
    print("   - Qualité: qualite_manager / Qualite@123")
    print("   - Réception: reception_manager / Reception@123")
    print("   - User: user / User@123")
    print("=" * 50)


# ==================== FONCTIONS UTILITAIRES ====================

def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, statut, last_login, created_at, fullname, telephone, departement FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, statut, last_login, created_at, fullname, telephone, departement FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_last_login(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                   (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()


def create_audit_log(user_id, user_name, user_role, action, entity_type, entity_id, details, ip_address, user_agent=None, old_data=None, new_data=None):
    """Crée une entrée dans les logs d'audit (base de données)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_logs (user_id, user_name, user_role, action, entity_type, entity_id, old_data, new_data, details, ip_address, user_agent, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, user_role, action, entity_type, entity_id, 
          json.dumps(old_data) if old_data else None, 
          json.dumps(new_data) if new_data else None, 
          details, ip_address, user_agent, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_audit_logs(limit=100, offset=0, action=None, user_id=None):
    """Récupère les logs d'audit depuis la base de données"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM audit_logs WHERE 1=1'
    params = []
    
    if action:
        query += ' AND action = ?'
        params.append(action)
    if user_id:
        query += ' AND user_id = ?'
        params.append(user_id)
    
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return logs


def create_session(user_id, token, ip_address, user_agent):
    """Crée une session utilisateur"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_sessions (user_id, token, ip_address, user_agent, login_at, last_activity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, token, ip_address, user_agent, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def update_session_activity(token):
    """Met à jour la dernière activité d'une session"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_sessions SET last_activity = ? WHERE token = ? AND logout_at IS NULL
    ''', (datetime.now().isoformat(), token))
    conn.commit()
    conn.close()


def end_session(token):
    """Termine une session"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_sessions SET logout_at = ? WHERE token = ? AND logout_at IS NULL
    ''', (datetime.now().isoformat(), token))
    conn.commit()
    conn.close()


def get_active_sessions():
    """Récupère toutes les sessions actives"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, u.username, u.role 
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.logout_at IS NULL
        ORDER BY s.last_activity DESC
    ''')
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions


def create_notification(user_id, title, message, type='info'):
    """Crée une notification pour un utilisateur"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications (user_id, title, message, type, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, title, message, type, datetime.now().isoformat()))
    conn.commit()
    notif_id = cursor.lastrowid
    conn.close()
    return notif_id


def get_user_notifications(user_id, limit=20, unread_only=False):
    """Récupère les notifications d'un utilisateur"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM notifications WHERE user_id = ?'
    params = [user_id]
    
    if unread_only:
        query += ' AND read = 0'
    
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    notifications = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notifications


def mark_notification_read(notification_id):
    """Marque une notification comme lue"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE notifications SET read = 1, read_at = ? WHERE id = ?
    ''', (datetime.now().isoformat(), notification_id))
    conn.commit()
    conn.close()


def get_stock_alerts():
    """Récupère les alertes de stock"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM stock_items 
        WHERE quantite <= stock_min 
        ORDER BY quantite ASC
    ''')
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alerts


def get_reception_file_path(reception_id):
    """Récupère le chemin du fichier de réception"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT chemin_fichier, nom FROM commandes_recues WHERE id = ?', (reception_id,))
    reception = cursor.fetchone()
    conn.close()
    return dict(reception) if reception else None