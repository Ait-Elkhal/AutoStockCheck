"""
Ajout des tables d'audit et de traçabilité
AutoStockCheck - ECU Worldwide
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/database/autostockcheck.db')

def add_audit_tables():
    """Ajoute les tables d'audit et les colonnes de traçabilité"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ==================== TABLE AUDIT LOGS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            user_role TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            old_data TEXT,
            new_data TEXT,
            ip_address TEXT,
            user_agent TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ==================== AJOUTER COLONNES À COMMANDES_RECUES ====================
    cursor.execute("PRAGMA table_info(commandes_recues)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    if 'created_by' not in existing_columns:
        cursor.execute("ALTER TABLE commandes_recues ADD COLUMN created_by INTEGER")
        cursor.execute("ALTER TABLE commandes_recues ADD COLUMN created_by_name TEXT")
        cursor.execute("ALTER TABLE commandes_recues ADD COLUMN modified_by INTEGER")
        cursor.execute("ALTER TABLE commandes_recues ADD COLUMN modified_by_name TEXT")
        cursor.execute("ALTER TABLE commandes_recues ADD COLUMN modified_at TEXT")
        print("✅ Colonnes de traçabilité ajoutées à commandes_recues")
    
    # ==================== AJOUTER COLONNES À FACTURES_RECUES ====================
    cursor.execute("PRAGMA table_info(factures_recues)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    if 'created_by' not in existing_columns:
        cursor.execute("ALTER TABLE factures_recues ADD COLUMN created_by INTEGER")
        cursor.execute("ALTER TABLE factures_recues ADD COLUMN created_by_name TEXT")
        print("✅ Colonnes de traçabilité ajoutées à factures_recues")
    
    # ==================== TABLE SESSIONS UTILISATEURS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP,
            logout_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ==================== TABLE ACTIVITÉS QUOTIDIENNES ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            total_commands INTEGER DEFAULT 0,
            total_receptions INTEGER DEFAULT 0,
            total_factures INTEGER DEFAULT 0,
            total_users_active INTEGER DEFAULT 0,
            unique_ips TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Tables d'audit créées avec succès")
    print("   - audit_logs")
    print("   - user_sessions")
    print("   - daily_activity")

if __name__ == "__main__":
    add_audit_tables()