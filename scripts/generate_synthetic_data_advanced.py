"""
Générateur de données synthétiques avancé avec features enrichies
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import pandas as pd
import random
import os
import sys
from datetime import datetime, timedelta

print(f"Python version: {sys.version}")

# Configuration
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ==================== PRODUITS ENRICHIS ====================

PRODUITS = [
    # reference, nom, categorie, prix, stock_moyen, etat_moyen, popularite, fournisseur
    {"reference": "REF-001", "nom": "Ordinateur portable", "categorie": "Informatique", 
     "prix": 899.99, "stock_moyen": 50, "etat_moyen": 0.95, "popularite": 0.9, "fournisseur": "Dell"},
    {"reference": "REF-002", "nom": "Souris sans fil", "categorie": "Périphérique", 
     "prix": 25.00, "stock_moyen": 200, "etat_moyen": 0.98, "popularite": 0.85, "fournisseur": "Logitech"},
    {"reference": "REF-003", "nom": "Clavier mécanique", "categorie": "Périphérique", 
     "prix": 79.90, "stock_moyen": 100, "etat_moyen": 0.97, "popularite": 0.7, "fournisseur": "Corsair"},
    {"reference": "REF-004", "nom": "Écran 24 pouces", "categorie": "Informatique", 
     "prix": 199.99, "stock_moyen": 30, "etat_moyen": 0.94, "popularite": 0.75, "fournisseur": "Samsung"},
    {"reference": "REF-005", "nom": "Disque SSD 1To", "categorie": "Stockage", 
     "prix": 89.99, "stock_moyen": 80, "etat_moyen": 0.99, "popularite": 0.8, "fournisseur": "Samsung"},
    {"reference": "REF-006", "nom": "Mémoire RAM 16Go", "categorie": "Composant", 
     "prix": 59.99, "stock_moyen": 60, "etat_moyen": 0.99, "popularite": 0.65, "fournisseur": "Corsair"},
    {"reference": "REF-007", "nom": "Câble HDMI", "categorie": "Accessoire", 
     "prix": 9.99, "stock_moyen": 500, "etat_moyen": 0.99, "popularite": 0.6, "fournisseur": "Belkin"},
    {"reference": "REF-008", "nom": "Webcam HD", "categorie": "Périphérique", 
     "prix": 49.99, "stock_moyen": 40, "etat_moyen": 0.96, "popularite": 0.55, "fournisseur": "Logitech"},
    {"reference": "REF-009", "nom": "Casque audio", "categorie": "Audio", 
     "prix": 39.99, "stock_moyen": 70, "etat_moyen": 0.95, "popularite": 0.7, "fournisseur": "Sony"},
    {"reference": "REF-010", "nom": "Tablette graphique", "categorie": "Périphérique", 
     "prix": 129.99, "stock_moyen": 25, "etat_moyen": 0.97, "popularite": 0.5, "fournisseur": "Wacom"},
    {"reference": "REF-011", "nom": "Imprimante laser", "categorie": "Imprimante", 
     "prix": 249.99, "stock_moyen": 15, "etat_moyen": 0.93, "popularite": 0.45, "fournisseur": "HP"},
    {"reference": "REF-012", "nom": "Papier A4", "categorie": "Consommable", 
     "prix": 12.99, "stock_moyen": 300, "etat_moyen": 1.0, "popularite": 0.8, "fournisseur": "HP"},
    {"reference": "REF-013", "nom": "Toner imprimante", "categorie": "Consommable", 
     "prix": 89.99, "stock_moyen": 50, "etat_moyen": 0.98, "popularite": 0.6, "fournisseur": "HP"},
    {"reference": "REF-014", "nom": "Support mural", "categorie": "Accessoire", 
     "prix": 34.99, "stock_moyen": 60, "etat_moyen": 0.99, "popularite": 0.4, "fournisseur": "Generic"},
    {"reference": "REF-015", "nom": "Station d'accueil", "categorie": "Accessoire", 
     "prix": 149.99, "stock_moyen": 20, "etat_moyen": 0.96, "popularite": 0.5, "fournisseur": "Dell"},
    {"reference": "REF-016", "nom": "Microphone USB", "categorie": "Audio", 
     "prix": 59.99, "stock_moyen": 45, "etat_moyen": 0.97, "popularite": 0.55, "fournisseur": "Blue"},
    {"reference": "REF-017", "nom": "Routeur WiFi", "categorie": "Réseau", 
     "prix": 79.99, "stock_moyen": 35, "etat_moyen": 0.95, "popularite": 0.7, "fournisseur": "TP-Link"},
    {"reference": "REF-018", "nom": "Switch réseau", "categorie": "Réseau", 
     "prix": 29.99, "stock_moyen": 55, "etat_moyen": 0.98, "popularite": 0.5, "fournisseur": "Netgear"},
    {"reference": "REF-019", "nom": "Onduleur", "categorie": "Énergie", 
     "prix": 129.99, "stock_moyen": 25, "etat_moyen": 0.94, "popularite": 0.4, "fournisseur": "APC"},
    {"reference": "REF-020", "nom": "Disque dur externe", "categorie": "Stockage", 
     "prix": 79.99, "stock_moyen": 65, "etat_moyen": 0.98, "popularite": 0.75, "fournisseur": "Seagate"},
]


def generer_etat_produit(etat_moyen):
    """Génère l'état du produit avec une variation aléatoire"""
    # État entre 0.7 et 1.0 avec une moyenne autour de etat_moyen
    etat = np.random.normal(etat_moyen, 0.05)
    etat = np.clip(etat, 0.7, 1.0)
    
    # Détérioration possible pour les produits en fin de vie
    if random.random() < 0.1:
        etat -= random.uniform(0.05, 0.2)
    
    return round(etat, 2)


def generer_date_commande():
    """Génère une date de commande aléatoire"""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 3, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def generer_facture(nb_lignes_min=1, nb_lignes_max=10):
    """Génère une facture client avec date et priorité"""
    nb_lignes = random.randint(nb_lignes_min, nb_lignes_max)
    produits_selectionnes = random.sample(PRODUITS, nb_lignes)
    
    date_commande = generer_date_commande()
    priorite = random.choice(['basse', 'moyenne', 'haute', 'urgente'])
    
    lignes = []
    for produit in produits_selectionnes:
        # Quantité influencée par la popularité
        quantite_base = random.randint(1, 30)
        quantite = int(quantite_base * produit["popularite"])
        quantite = max(1, quantite)
        
        lignes.append({
            "reference": produit["reference"],
            "produit": produit["nom"],
            "quantite": quantite,
            "prix_unitaire": produit["prix"],
            "categorie": produit["categorie"],
            "stock_moyen": produit["stock_moyen"],
            "etat_moyen": produit["etat_moyen"],
            "popularite": produit["popularite"],
            "fournisseur": produit["fournisseur"],
            "date_commande": date_commande,
            "priorite": priorite
        })
    
    return lignes


def generer_stock_reel(facture_lignes, taux_manque_reel=0.15):
    """Génère le stock réel avec toutes les nouvelles features"""
    stock = []
    
    for ligne in facture_lignes:
        reference = ligne["reference"]
        quantite_facture = ligne["quantite"]
        stock_moyen = ligne["stock_moyen"]
        etat_moyen = ligne["etat_moyen"]
        popularite = ligne["popularite"]
        fournisseur = ligne["fournisseur"]
        date_commande = ligne["date_commande"]
        priorite = ligne["priorite"]
        
        # 1. État du produit réel
        etat_reel = generer_etat_produit(etat_moyen)
        
        # 2. Probabilité de rupture influencée par plusieurs facteurs
        prob_rupture_base = max(0, 1 - (stock_moyen / quantite_facture)) if quantite_facture > 0 else 0.5
        prob_rupture = prob_rupture_base * (1 - etat_reel) * (1 - popularite)
        prob_rupture = min(0.4, prob_rupture)
        
        # 3. Fiabilité du fournisseur
        fiabilite_fournisseur = {
            'Dell': 0.95, 'Logitech': 0.98, 'Corsair': 0.97, 'Samsung': 0.99,
            'Belkin': 0.92, 'Sony': 0.96, 'Wacom': 0.94, 'HP': 0.93,
            'Generic': 0.85, 'Blue': 0.95, 'TP-Link': 0.96, 'Netgear': 0.94,
            'APC': 0.97, 'Seagate': 0.95
        }.get(fournisseur, 0.90)
        
        # 4. Saisonnalité (Noël, rentrée, etc.)
        mois = date_commande.month
        saisonnalite = 1.0
        if mois in [11, 12]:  # Période de Noël
            saisonnalite = 1.3
        elif mois in [9, 10]:  # Rentrée
            saisonnalite = 1.2
        elif mois in [1, 2]:  # Post-Noël
            saisonnalite = 0.8
        
        # 5. Priorité de commande
        priorite_factor = {'basse': 0.8, 'moyenne': 1.0, 'haute': 1.2, 'urgente': 1.5}.get(priorite, 1.0)
        
        # Calcul du stock réel
        rupture = random.random() < (prob_rupture * saisonnalite / priorite_factor)
        
        if rupture:
            if random.random() < 0.4:
                quantite_reelle = 0
                type_manque = "rupture_totale"
            else:
                quantite_reelle = random.randint(1, max(1, quantite_facture - 1))
                type_manque = "rupture_partielle"
        else:
            quantite_reelle = quantite_facture
            type_manque = "aucun"
        
        # Problème de qualité (produit défectueux)
        if etat_reel < 0.8 and random.random() < 0.1:
            quantite_reelle = max(0, quantite_reelle - random.randint(1, 2))
            type_manque = "defaut_qualite"
        
        # Problème fournisseur
        if random.random() > fiabilite_fournisseur and quantite_reelle > 0:
            quantite_reelle = max(0, quantite_reelle - random.randint(1, 3))
            type_manque = "retard_fournisseur"
        
        quantite_reelle = max(0, quantite_reelle)
        
        is_manque = quantite_reelle < quantite_facture
        
        stock.append({
            "reference": reference,
            "produit": ligne["produit"],
            "quantite": quantite_reelle,
            "quantite_facture": quantite_facture,
            "emplacement": f"ZONE-{random.choice(['A','B','C','D','E'])}{random.randint(1,30)}",
            "etat_produit": etat_reel,
            "fournisseur": fournisseur,
            "date_commande": date_commande,
            "priorite": priorite,
            "manque": is_manque,
            "type_manque": type_manque if is_manque else "aucun",
            "difference": quantite_facture - quantite_reelle
        })
    
    return stock


def generer_dataset_entrainement(n_echantillons=5000):
    """Génère un dataset avec toutes les nouvelles features"""
    donnees = []
    
    for i in range(n_echantillons):
        facture = generer_facture()
        stock = generer_stock_reel(facture, taux_manque_reel=0.15)
        
        for ligne_facture, ligne_stock in zip(facture, stock):
            # Features de base
            diff_quantite = ligne_facture["quantite"] - ligne_stock["quantite"]
            produit_absent = 1 if ligne_stock["quantite"] == 0 else 0
            quantite_insuffisante = 1 if diff_quantite > 0 else 0
            ratio_stock = ligne_stock["quantite"] / ligne_facture["quantite"] if ligne_facture["quantite"] > 0 else 0
            
            # NOUVELLES FEATURES
            # 1. État du produit
            etat_produit = ligne_stock["etat_produit"]
            
            # 2. Fiabilité du fournisseur
            fiabilite_fournisseur = {
                'Dell': 0.95, 'Logitech': 0.98, 'Corsair': 0.97, 'Samsung': 0.99,
                'Belkin': 0.92, 'Sony': 0.96, 'Wacom': 0.94, 'HP': 0.93,
                'Generic': 0.85, 'Blue': 0.95, 'TP-Link': 0.96, 'Netgear': 0.94,
                'APC': 0.97, 'Seagate': 0.95
            }.get(ligne_stock["fournisseur"], 0.90)
            
            # 3. Popularité du produit
            popularite = ligne_facture["popularite"]
            
            # 4. Saisonnalité
            mois = ligne_stock["date_commande"].month
            saisonnalite = 1.0
            if mois in [11, 12]:
                saisonnalite = 1.3
            elif mois in [9, 10]:
                saisonnalite = 1.2
            elif mois in [1, 2]:
                saisonnalite = 0.8
            
            # 5. Priorité de commande
            priorite_encoded = {'basse': 0, 'moyenne': 1, 'haute': 2, 'urgente': 3}.get(ligne_stock["priorite"], 1)
            
            # 6. Valeur totale de la ligne
            valeur_ligne = ligne_facture["quantite"] * ligne_facture["prix_unitaire"]
            
            # 7. Produit cher (prix > 100€)
            produit_cher = 1 if ligne_facture["prix_unitaire"] > 100 else 0
            
            # 8. Interactions
            diff_x_prix = diff_quantite * ligne_facture["prix_unitaire"]
            absent_x_prix = produit_absent * ligne_facture["prix_unitaire"]
            etat_x_popularite = etat_produit * popularite
            
            label = 1 if ligne_stock["manque"] else 0
            
            donnees.append({
                "id_echantillon": i,
                "reference": ligne_facture["reference"],
                "produit": ligne_facture["produit"],
                "categorie": ligne_facture["categorie"],
                
                # Features existantes
                "quantite_facture": ligne_facture["quantite"],
                "quantite_stock": ligne_stock["quantite"],
                "diff_quantite": diff_quantite,
                "produit_absent": produit_absent,
                "quantite_insuffisante": quantite_insuffisante,
                "ratio_stock": ratio_stock,
                "prix": ligne_facture["prix_unitaire"],
                
                # NOUVELLES FEATURES
                "etat_produit": etat_produit,
                "fiabilite_fournisseur": fiabilite_fournisseur,
                "popularite": popularite,
                "saisonnalite": saisonnalite,
                "priorite": priorite_encoded,
                "valeur_ligne": valeur_ligne,
                "produit_cher": produit_cher,
                "diff_x_prix": diff_x_prix,
                "absent_x_prix": absent_x_prix,
                "etat_x_popularite": etat_x_popularite,
                
                "label": label
            })
    
    return pd.DataFrame(donnees)


def generer_fichiers_excel(nb_fichiers=100):
    """Génère des fichiers Excel avec toutes les nouvelles colonnes"""
    os.makedirs("data/datasets", exist_ok=True)
    
    for i in range(1, nb_fichiers + 1):
        facture = generer_facture(nb_lignes_min=2, nb_lignes_max=8)
        stock = generer_stock_reel(facture, taux_manque_reel=0.15)
        
        df_facture = pd.DataFrame(facture)
        df_facture = df_facture[["reference", "produit", "quantite", "prix_unitaire", "categorie", "date_commande", "priorite"]]
        
        df_stock = pd.DataFrame(stock)
        df_stock = df_stock[["reference", "produit", "quantite", "etat_produit", "fournisseur", "emplacement", "difference", "manque"]]
        
        df_facture.to_excel(f"data/datasets/facture_{i:03d}.xlsx", index=False)
        df_stock.to_excel(f"data/datasets/stock_{i:03d}.xlsx", index=False)
    
    print(f"✅ {nb_fichiers} fichiers Excel générés dans data/datasets/")


# ==================== EXÉCUTION ====================

if __name__ == "__main__":
    print("=" * 60)
    print("GÉNÉRATION DE DONNÉES AVEC FEATURES ENRICHIES")
    print("AutoStockCheck - ECU Worldwide")
    print("=" * 60)
    
    # 1. Générer le dataset d'entraînement
    print("\n📊 Génération du dataset enrichi...")
    dataset = generer_dataset_entrainement(5000)
    print(f"   ✅ Dataset généré : {len(dataset)} lignes")
    print(f"   📈 Conformes (label=0) : {len(dataset[dataset['label']==0])} ({len(dataset[dataset['label']==0])/len(dataset)*100:.1f}%)")
    print(f"   ⚠️ Manques (label=1) : {len(dataset[dataset['label']==1])} ({len(dataset[dataset['label']==1])/len(dataset)*100:.1f}%)")
    
    # Afficher les nouvelles features
    print(f"\n📋 Nouvelles features ajoutées:")
    nouvelles_features = ['etat_produit', 'fiabilite_fournisseur', 'popularite', 'saisonnalite', 
                          'priorite', 'valeur_ligne', 'produit_cher', 'diff_x_prix', 'absent_x_prix', 'etat_x_popularite']
    for feat in nouvelles_features:
        print(f"   ✅ {feat}")
    
    os.makedirs("data/datasets", exist_ok=True)
    dataset.to_csv("data/datasets/dataset_entrainement.csv", index=False)
    print(f"\n   💾 Sauvegardé dans data/datasets/dataset_entrainement.csv")
    
    # 2. Générer les fichiers Excel de test
    print("\n📁 Génération des fichiers Excel de test...")
    generer_fichiers_excel(100)
    
    # 3. Statistiques
    print("\n" + "=" * 60)
    print("STATISTIQUES DU DATASET ENRICHI")
    print("=" * 60)
    
    print(f"\n📊 Distribution des labels :")
    print(f"   Conformes (0) : {len(dataset[dataset['label']==0])} ({len(dataset[dataset['label']==0])/len(dataset)*100:.1f}%)")
    print(f"   Manques (1)   : {len(dataset[dataset['label']==1])} ({len(dataset[dataset['label']==1])/len(dataset)*100:.1f}%)")
    
    print(f"\n📊 Statistiques des nouvelles features :")
    print(f"   État produit moyen : {dataset['etat_produit'].mean():.3f}")
    print(f"   Fiabilité fournisseur moyenne : {dataset['fiabilite_fournisseur'].mean():.3f}")
    print(f"   Popularité moyenne : {dataset['popularite'].mean():.3f}")
    print(f"   Saisonnalité moyenne : {dataset['saisonnalite'].mean():.3f}")
    print(f"   Priorité moyenne : {dataset['priorite'].mean():.2f}")
    print(f"   Valeur ligne moyenne : {dataset['valeur_ligne'].mean():.2f}€")
    print(f"   Produits chers : {dataset['produit_cher'].sum()} ({dataset['produit_cher'].mean()*100:.1f}%)")
    
    print("\n" + "=" * 60)
    print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 60)