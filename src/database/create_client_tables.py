"""
ÉTAPE 1: Création des tables pour la gestion des clients
AutoStockCheck - ECU Worldwide
Exécuter ce script en premier
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/database/autostockcheck.db')

def create_tables():
    """Crée toutes les tables nécessaires pour la gestion des clients"""
    
    # Créer le dossier database si nécessaire
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ==================== TABLE DES CLIENTS EXTERNES ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients_externes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT,
            sexe TEXT,
            nationalite TEXT,
            telephone TEXT,
            adresse TEXT,
            dossier_path TEXT,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'actif'
        )
    ''')
    print("✅ Table 'clients_externes' créée")
    
    # ==================== TABLE DES EMAILS ÉCHANGÉS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            direction TEXT NOT NULL,
            sujet TEXT NOT NULL,
            contenu TEXT,
            pieces_jointes TEXT,
            message_id TEXT,
            reference_facture TEXT,
            date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'envoye',
            FOREIGN KEY (client_id) REFERENCES clients_externes(id)
        )
    ''')
    print("✅ Table 'emails_clients' créée")
    
    # ==================== TABLE DES FACTURES CLIENTS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factures_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            reference TEXT NOT NULL,
            chemin_fichier TEXT NOT NULL,
            date_reception TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_facture TEXT,
            montant_total REAL,
            statut TEXT DEFAULT 'recue',
            contenu_extraie TEXT,
            FOREIGN KEY (client_id) REFERENCES clients_externes(id)
        )
    ''')
    print("✅ Table 'factures_clients' créée")
    
    # ==================== TABLE DES RAPPORTS ENVOYÉS ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rapports_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            type_rapport TEXT NOT NULL,
            chemin_fichier TEXT,
            date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            contenu TEXT,
            statut TEXT DEFAULT 'envoye',
            FOREIGN KEY (client_id) REFERENCES clients_externes(id)
        )
    ''')
    print("✅ Table 'rapports_clients' créée")
    
    # ==================== TABLE DE L'HISTORIQUE ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historique_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur TEXT,
            FOREIGN KEY (client_id) REFERENCES clients_externes(id)
        )
    ''')
    print("✅ Table 'historique_clients' créée")
    
    # ==================== TABLE DE L'AGENDA ====================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agenda_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            date_evenement TIMESTAMP NOT NULL,
            type_evenement TEXT NOT NULL,
            reference TEXT,
            statut TEXT DEFAULT 'planifie',
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients_externes(id)
        )
    ''')
    print("✅ Table 'agenda_clients' créée")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ Toutes les tables ont été créées avec succès !")
    print("=" * 50)
    print("\nTables créées:")
    print("  1. clients_externes     - Informations des clients")
    print("  2. emails_clients       - Emails échangés")
    print("  3. factures_clients     - Factures reçues")
    print("  4. rapports_clients     - Rapports envoyés")
    print("  5. historique_clients   - Historique des actions")
    print("  6. agenda_clients       - Agenda des événements")

def create_client_folders():
    """Crée la structure de dossiers pour les clients"""
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    CLIENTS_ROOT = os.path.join(BASE_DIR, 'data', 'clients')
    
    os.makedirs(CLIENTS_ROOT, exist_ok=True)
    print(f"\n📁 Dossier clients créé: {CLIENTS_ROOT}")
    
    return CLIENTS_ROOT

if __name__ == "__main__":
    print("=" * 50)
    print("📦 AutoStockCheck - Création des tables clients")
    print("=" * 50 + "\n")
    
    create_tables()
    create_client_folders()
    
    print("\n✅ ÉTAPE 1 terminée !")
    print("   Maintenant, exécutez votre serveur Flask et passez à l'ÉTAPE 2.")