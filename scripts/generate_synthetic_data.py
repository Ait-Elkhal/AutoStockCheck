"""
Générateur de données synthétiques pour l'entraînement des modèles ML
AutoStockCheck - ECU Worldwide
Python 3.10
"""

import numpy as np
import pandas as pd
import random
import os
import sys

print(f"Python version: {sys.version}")
print(f"NumPy version: {np.__version__}")
print(f"Pandas version: {pd.__version__}")

# Configuration
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ==================== PRODUITS DE TEST ====================

PRODUITS = [
    {"reference": "REF-001", "nom": "Ordinateur portable", "categorie": "Informatique", "prix": 899.99, "frequence": 0.15},
    {"reference": "REF-002", "nom": "Souris sans fil", "categorie": "Périphérique", "prix": 25.00, "frequence": 0.12},
    {"reference": "REF-003", "nom": "Clavier mécanique", "categorie": "Périphérique", "prix": 79.90, "frequence": 0.10},
    {"reference": "REF-004", "nom": "Écran 24 pouces", "categorie": "Informatique", "prix": 199.99, "frequence": 0.08},
    {"reference": "REF-005", "nom": "Disque SSD 1To", "categorie": "Stockage", "prix": 89.99, "frequence": 0.10},
    {"reference": "REF-006", "nom": "Mémoire RAM 16Go", "categorie": "Composant", "prix": 59.99, "frequence": 0.07},
    {"reference": "REF-007", "nom": "Câble HDMI", "categorie": "Accessoire", "prix": 9.99, "frequence": 0.05},
    {"reference": "REF-008", "nom": "Webcam HD", "categorie": "Périphérique", "prix": 49.99, "frequence": 0.06},
    {"reference": "REF-009", "nom": "Casque audio", "categorie": "Audio", "prix": 39.99, "frequence": 0.08},
    {"reference": "REF-010", "nom": "Tablette graphique", "categorie": "Périphérique", "prix": 129.99, "frequence": 0.04},
    {"reference": "REF-011", "nom": "Imprimante laser", "categorie": "Imprimante", "prix": 249.99, "frequence": 0.03},
    {"reference": "REF-012", "nom": "Papier A4 500 feuilles", "categorie": "Consommable", "prix": 12.99, "frequence": 0.04},
    {"reference": "REF-013", "nom": "Toner imprimante", "categorie": "Consommable", "prix": 89.99, "frequence": 0.03},
    {"reference": "REF-014", "nom": "Support mural écran", "categorie": "Accessoire", "prix": 34.99, "frequence": 0.02},
    {"reference": "REF-015", "nom": "Station d'accueil USB-C", "categorie": "Accessoire", "prix": 149.99, "frequence": 0.03},
]


def generer_facture(nb_lignes_min=1, nb_lignes_max=8):
    """Génère une facture client aléatoire"""
    nb_lignes = random.randint(nb_lignes_min, nb_lignes_max)
    produits_selectionnes = random.sample(PRODUITS, nb_lignes)
    
    lignes = []
    for produit in produits_selectionnes:
        quantite = random.randint(1, 20)
        lignes.append({
            "reference": produit["reference"],
            "produit": produit["nom"],
            "quantite": quantite,
            "prix_unitaire": produit["prix"],
            "categorie": produit["categorie"]
        })
    
    return lignes


def generer_stock_reel(facture_lignes, taux_manque=0.25, taux_erreur=0.05):
    """Génère la liste du stock réel basée sur la facture"""
    stock = []
    
    for ligne in facture_lignes:
        reference = ligne["reference"]
        quantite_facture = ligne["quantite"]
        
        a_manque = random.random() < taux_manque
        
        if a_manque:
            if random.random() < 0.3:
                quantite_reelle = 0
                type_manque = "total"
            else:
                quantite_reelle = random.randint(1, max(1, quantite_facture - 1))
                type_manque = "partiel"
        else:
            quantite_reelle = quantite_facture
            type_manque = "aucun"
        
        if random.random() < taux_erreur and not a_manque:
            quantite_reelle = quantite_facture + random.randint(1, 5)
        
        quantite_reelle = max(0, quantite_reelle)
        
        stock.append({
            "reference": reference,
            "produit": ligne["produit"],
            "quantite": quantite_reelle,
            "emplacement": f"ZONE-{random.choice(['A','B','C'])}{random.randint(1,20)}",
            "manque": quantite_reelle < quantite_facture,
            "type_manque": type_manque if quantite_reelle < quantite_facture else "aucun",
            "difference": quantite_facture - quantite_reelle
        })
    
    return stock


def generer_dataset_entrainement(n_echantillons=1000):
    """Génère un dataset complet pour l'entraînement"""
    donnees = []
    
    for i in range(n_echantillons):
        facture = generer_facture()
        stock = generer_stock_reel(facture, taux_manque=0.30, taux_erreur=0.05)
        
        for ligne_facture, ligne_stock in zip(facture, stock):
            diff_quantite = ligne_facture["quantite"] - ligne_stock["quantite"]
            produit_absent = 1 if ligne_stock["quantite"] == 0 else 0
            quantite_insuffisante = 1 if diff_quantite > 0 else 0
            label = 1 if ligne_stock["manque"] else 0
            
            donnees.append({
                "id_echantillon": i,
                "reference": ligne_facture["reference"],
                "produit": ligne_facture["produit"],
                "categorie": ligne_facture["categorie"],
                "quantite_facture": ligne_facture["quantite"],
                "quantite_stock": ligne_stock["quantite"],
                "diff_quantite": diff_quantite,
                "produit_absent": produit_absent,
                "quantite_insuffisante": quantite_insuffisante,
                "prix": ligne_facture["prix_unitaire"],
                "label": label
            })
    
    return pd.DataFrame(donnees)


def generer_fichiers_excel(nb_fichiers=50):
    """Génère des fichiers Excel d'exemple pour les tests"""
    os.makedirs("data/datasets", exist_ok=True)
    
    for i in range(1, nb_fichiers + 1):
        facture = generer_facture(nb_lignes_min=2, nb_lignes_max=6)
        stock = generer_stock_reel(facture, taux_manque=0.3)
        
        df_facture = pd.DataFrame(facture)
        df_facture = df_facture[["reference", "produit", "quantite", "prix_unitaire", "categorie"]]
        
        df_stock = pd.DataFrame(stock)
        df_stock = df_stock[["reference", "produit", "quantite", "emplacement", "difference", "manque"]]
        
        df_facture.to_excel(f"data/datasets/facture_{i:03d}.xlsx", index=False)
        df_stock.to_excel(f"data/datasets/stock_{i:03d}.xlsx", index=False)
    
    print(f"✅ {nb_fichiers} fichiers Excel générés dans data/datasets/")


# ==================== EXÉCUTION PRINCIPALE ====================

if __name__ == "__main__":
    print("=" * 50)
    print("GÉNÉRATION DE DONNÉES SYNTHÉTIQUES")
    print("AutoStockCheck - ECU Worldwide")
    print("=" * 50)
    
    # 1. Générer le dataset d'entraînement
    print("\n📊 Génération du dataset d'entraînement...")
    dataset = generer_dataset_entrainement(1000)
    print(f"   ✅ Dataset généré : {len(dataset)} lignes")
    print(f"   📈 Conformes (label=0) : {len(dataset[dataset['label']==0])}")
    print(f"   ⚠️ Manques (label=1) : {len(dataset[dataset['label']==1])}")
    
    os.makedirs("data/datasets", exist_ok=True)
    dataset.to_csv("data/datasets/dataset_entrainement.csv", index=False)
    print(f"   💾 Sauvegardé dans data/datasets/dataset_entrainement.csv")
    
    # 2. Générer les fichiers Excel de test
    print("\n📁 Génération des fichiers Excel de test...")
    generer_fichiers_excel(50)
    
    # 3. Statistiques
    print("\n" + "=" * 50)
    print("STATISTIQUES DU DATASET")
    print("=" * 50)
    
    print(f"\n📊 Distribution des labels :")
    print(f"   Conformes (0) : {len(dataset[dataset['label']==0])} ({len(dataset[dataset['label']==0])/len(dataset)*100:.1f}%)")
    print(f"   Manques (1)   : {len(dataset[dataset['label']==1])} ({len(dataset[dataset['label']==1])/len(dataset)*100:.1f}%)")
    
    print(f"\n📊 Statistiques des features :")
    print(f"   Différence quantité moyenne : {dataset['diff_quantite'].mean():.2f}")
    print(f"   Produits absents : {dataset['produit_absent'].sum()} ({dataset['produit_absent'].mean()*100:.1f}%)")
    print(f"   Quantités insuffisantes : {dataset['quantite_insuffisante'].sum()} ({dataset['quantite_insuffisante'].mean()*100:.1f}%)")
    
    print("\n" + "=" * 50)
    print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 50)