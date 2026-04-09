"""
Script pour générer des fichiers Excel compatibles avec l'extracteur AutoStockCheck
Colonnes exactes: "Référence" et "Quantité" pour la facture
"Référence" et "Quantité reçue" pour la réception
"""

import pandas as pd
import os

# Configuration
FICHIER_FACTURE = "facture_REC-001.xlsx"
FICHIER_RECEPTION = "reception_REC-001.xlsx"
REFERENCE = "REC-001"


def creer_facture():
    """Crée la facture avec les colonnes exactes attendues par l'extracteur"""
    print(f"📄 Création de la facture: {FICHIER_FACTURE}")
    
    # Données avec colonnes exactes
    data = {
        "Référence": ["REF-001", "REF-002", "REF-003", "REF-004", "REF-005"],
        "Produit": [
            "Ordinateur portable Dell XPS", 
            "Souris sans fil Logitech MX Master", 
            "Clavier mécanique Corsair K95", 
            "Écran 24 pouces Samsung", 
            "Disque SSD 1To Samsung"
        ],
        "Quantité": [5, 10, 3, 2, 4],
        "Prix unitaire": [899.99, 25.00, 79.90, 199.99, 89.99],
        "Total": [4499.95, 250.00, 239.70, 399.98, 359.96]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(FICHIER_FACTURE, index=False, engine='openpyxl')
    
    print(f"✅ Facture créée avec colonnes: {list(df.columns)}")
    print(f"   - Colonne 'Référence' présente ✅")
    print(f"   - Colonne 'Quantité' présente ✅")
    return FICHIER_FACTURE


def creer_reception():
    """Crée la réception avec les colonnes exactes attendues par l'extracteur"""
    print(f"\n📦 Création de la réception: {FICHIER_RECEPTION}")
    
    # Données avec colonnes exactes
    data = {
        "Référence": ["REF-001", "REF-002", "REF-003", "REF-004", "REF-006"],
        "Produit": [
            "Ordinateur portable Dell XPS", 
            "Souris sans fil Logitech MX Master", 
            "Clavier mécanique Corsair K95", 
            "Écran 24 pouces Samsung", 
            "Disque dur externe 2To"
        ],
        "Quantité reçue": [5, 8, 3, 2, 4],
        "Description": [
            "Dell XPS 15, i7, 16Go RAM, 1To SSD",
            "Logitech MX Master 3S, sans fil",
            "Corsair K95 RGB Platinum, mécanique",
            "Samsung Odyssey G3, 144Hz",
            "Seagate Expansion, USB 3.0"
        ],
        "État": ["Neuf", "Neuf", "Neuf", "Très bon", "Bon"],
        "Prix unitaire": [899.99, 25.00, 79.90, 199.99, 89.99]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(FICHIER_RECEPTION, index=False, engine='openpyxl')
    
    print(f"✅ Réception créée avec colonnes: {list(df.columns)}")
    print(f"   - Colonne 'Référence' présente ✅")
    print(f"   - Colonne 'Quantité reçue' présente ✅")
    return FICHIER_RECEPTION


def afficher_resume():
    """Affiche un résumé des différences pour la comparaison"""
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES DONNÉES POUR LA COMPARAISON")
    print("=" * 70)
    
    print("\n📄 FACTURE (REC-001):")
    print("-" * 60)
    facture_produits = [
        ("REF-001", "Ordinateur portable", 5),
        ("REF-002", "Souris sans fil", 10),
        ("REF-003", "Clavier mécanique", 3),
        ("REF-004", "Écran 24 pouces", 2),
        ("REF-005", "Disque SSD 1To", 4)
    ]
    for ref, nom, qte in facture_produits:
        print(f"   {ref} | {nom:<30} | Quantité: {qte}")
    
    print("\n📦 RÉCEPTION RÉELLE (REC-001):")
    print("-" * 60)
    reception_produits = [
        ("REF-001", "Ordinateur portable", 5),
        ("REF-002", "Souris sans fil", 8),
        ("REF-003", "Clavier mécanique", 3),
        ("REF-004", "Écran 24 pouces", 2),
        ("REF-006", "Disque dur externe", 4)
    ]
    for ref, nom, qte in reception_produits:
        print(f"   {ref} | {nom:<30} | Quantité: {qte}")
    
    print("\n" + "=" * 70)
    print("🔍 DIFFÉRENCES ATTENDUES LORS DE LA COMPARAISON:")
    print("=" * 70)
    print("   ✅ REF-001: Conforme (5 vs 5)")
    print("   ⚠️ REF-002: Manque de 2 unités (10 vs 8)")
    print("   ✅ REF-003: Conforme (3 vs 3)")
    print("   ✅ REF-004: Conforme (2 vs 2)")
    print("   ⚠️ REF-005: Manque total (4 vs 0) - NON REÇU")
    print("   📦 REF-006: Surplus (0 vs 4) - NON FACTURÉ")
    print("\n💡 Résultats attendus dans la section Matching:")
    print("   - 3 commandes conformes")
    print("   - 3 anomalies détectées (2 manques partiels + 1 manque total + 1 surplus)")
    print("=" * 70)


def verifier_fichiers():
    """Vérifie que les fichiers ont bien été créés et sont lisibles"""
    print("\n🔍 VÉRIFICATION DES FICHIERS:")
    print("-" * 40)
    
    for fichier in [FICHIER_FACTURE, FICHIER_RECEPTION]:
        if os.path.exists(fichier):
            taille = os.path.getsize(fichier)
            print(f"   ✅ {fichier} - {taille} octets")
            
            # Tester la lecture
            try:
                df_test = pd.read_excel(fichier, engine='openpyxl')
                print(f"      Colonnes: {list(df_test.columns)}")
                print(f"      Lignes: {len(df_test)}")
            except Exception as e:
                print(f"      ⚠️ Erreur de lecture: {e}")
        else:
            print(f"   ❌ {fichier} non trouvé")


def main():
    """Fonction principale"""
    print("=" * 70)
    print("🚀 GÉNÉRATION DES FICHIERS DE TEST COMPATIBLES")
    print("=" * 70)
    print("\n⚠️  Les fichiers générés ont les colonnes exactes attendues par l'extracteur:")
    print("   - Facture: 'Référence' et 'Quantité' (obligatoires)")
    print("   - Réception: 'Référence' et 'Quantité reçue' (obligatoires)")
    
    # Créer le dossier si nécessaire
    if not os.path.exists("data/test"):
        os.makedirs("data/test")
        print("\n📁 Dossier data/test créé")
    
    # Sauvegarder le répertoire courant et aller dans data/test
    original_dir = os.getcwd()
    os.chdir("data/test")
    
    try:
        facture = creer_facture()
        reception = creer_reception()
        
        verifier_fichiers()
        afficher_resume()
        
        print("\n" + "=" * 70)
        print("✅ FICHIERS GÉNÉRÉS AVEC SUCCÈS !")
        print("=" * 70)
        print(f"\n📁 Emplacement: {os.path.abspath('.')}")
        print(f"   - {facture}")
        print(f"   - {reception}")
        
        print("\n📋 INSTRUCTIONS POUR LE TEST:")
        print("   " + "-" * 50)
        print("   1. Allez dans la section 'Réception (Factures)'")
        print(f"   2. Cliquez sur 'Ajouter facture'")
        print(f"   3. Référence de réception: {REFERENCE}")
        print(f"   4. Sélectionnez le fichier: {facture}")
        print("   5. Validez l'ajout")
        print("\n   6. Allez dans la section 'Réception Réelle'")
        print(f"   7. Référence commande: {REFERENCE}")
        print(f"   8. Importez le fichier: {reception}")
        print("   9. Terminez la commande")
        print("\n   10. Allez dans la section 'Matching'")
        print("   11. Sélectionnez les deux fichiers")
        print("   12. Cliquez sur 'Comparer avec le modèle IA'")
        print("   " + "-" * 50)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        os.chdir(original_dir)
    
    return 0


if __name__ == "__main__":
    # Vérifier que pandas est installé
    try:
        import pandas
        import openpyxl
        print("✅ Bibliothèques requises installées")
    except ImportError as e:
        print(f"❌ Bibliothèque manquante: {e}")
        print("   Installez avec: pip install pandas openpyxl")
        exit(1)
    
    exit(main())