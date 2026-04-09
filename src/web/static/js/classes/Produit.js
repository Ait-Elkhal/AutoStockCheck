/**
 * Classe Produit - Gestion des produits en stock
 * AutoStockCheck - ECU Worldwide
 */

class Produit {
    constructor(id, reference, nom, categorie, prix, stockActuel, stockMin, emplacement) {
        this.id = id || Date.now();
        this.reference = reference;
        this.nom = nom;
        this.categorie = categorie || 'Non catégorisé';
        this.prix = prix || 0;
        this.stockActuel = stockActuel || 0;
        this.stockMin = stockMin || 5;
        this.emplacement = emplacement || '';
        this.created_at = new Date().toISOString();
        this.modified_at = new Date().toISOString();
    }

    // Vérifier si le stock est bas
    estStockBas() {
        return this.stockActuel <= this.stockMin;
    }

    // Calculer la valeur totale du stock
    valeurStock() {
        return this.stockActuel * this.prix;
    }

    // Mettre à jour le stock
    mettreAJourStock(nouvelleQuantite, raison = 'Ajustement') {
        const ancienStock = this.stockActuel;
        this.stockActuel = nouvelleQuantite;
        this.modified_at = new Date().toISOString();
        
        return {
            ancien: ancienStock,
            nouveau: nouvelleQuantite,
            difference: nouvelleQuantite - ancienStock,
            raison: raison
        };
    }

    // Convertir en objet JSON
    toJSON() {
        return {
            id: this.id,
            reference: this.reference,
            nom: this.nom,
            categorie: this.categorie,
            prix: this.prix,
            stockActuel: this.stockActuel,
            stockMin: this.stockMin,
            emplacement: this.emplacement,
            created_at: this.created_at,
            modified_at: this.modified_at
        };
    }

    // Créer un produit depuis un objet
    static fromJSON(data) {
        const produit = new Produit(
            data.id,
            data.reference,
            data.nom,
            data.categorie,
            data.prix,
            data.stockActuel,
            data.stockMin,
            data.emplacement
        );
        produit.created_at = data.created_at;
        produit.modified_at = data.modified_at;
        return produit;
    }
}

// Export pour utilisation globale
window.Produit = Produit;