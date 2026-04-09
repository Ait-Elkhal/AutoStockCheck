/**
 * Classe Livraison - Gestion des livraisons
 * AutoStockCheck - ECU Worldwide
 */

class Livraison {
    constructor(id, commandeRef, dateLivraison, heureLivraison, transporteur, chauffeur, statut = 'planifiee') {
        this.id = id || Date.now();
        this.commandeRef = commandeRef;
        this.dateLivraison = dateLivraison;
        this.heureLivraison = heureLivraison;
        this.transporteur = transporteur || 'À définir';
        this.chauffeur = chauffeur || 'Non assigné';
        this.statut = statut; // 'planifiee', 'en_cours', 'livree', 'retard', 'annulee'
        this.adresseLivraison = '';
        this.contact = '';
        this.notes = '';
        this.created_at = new Date().toISOString();
        this.modified_at = new Date().toISOString();
    }

    // Démarrer la livraison
    demarrer(chauffeur) {
        this.statut = 'en_cours';
        if (chauffeur) this.chauffeur = chauffeur;
        this.modified_at = new Date().toISOString();
        return this;
    }

    // Terminer la livraison
    terminer() {
        this.statut = 'livree';
        this.modified_at = new Date().toISOString();
        return this;
    }

    // Signaler un retard
    retarder(raison) {
        this.statut = 'retard';
        this.notes = raison;
        this.modified_at = new Date().toISOString();
        return this;
    }

    // Annuler la livraison
    annuler(raison) {
        this.statut = 'annulee';
        this.notes = raison;
        this.modified_at = new Date().toISOString();
        return this;
    }

    // Obtenir le libellé du statut
    getStatutLabel() {
        const labels = {
            'planifiee': '📅 Planifiée',
            'en_cours': '🚚 En cours',
            'livree': '✅ Livrée',
            'retard': '⚠️ En retard',
            'annulee': '❌ Annulée'
        };
        return labels[this.statut] || this.statut;
    }

    // Convertir en objet JSON
    toJSON() {
        return {
            id: this.id,
            commandeRef: this.commandeRef,
            dateLivraison: this.dateLivraison,
            heureLivraison: this.heureLivraison,
            transporteur: this.transporteur,
            chauffeur: this.chauffeur,
            statut: this.statut,
            adresseLivraison: this.adresseLivraison,
            contact: this.contact,
            notes: this.notes,
            created_at: this.created_at,
            modified_at: this.modified_at
        };
    }

    // Créer une livraison depuis un objet
    static fromJSON(data) {
        const livraison = new Livraison(
            data.id,
            data.commandeRef,
            data.dateLivraison,
            data.heureLivraison,
            data.transporteur,
            data.chauffeur,
            data.statut
        );
        livraison.adresseLivraison = data.adresseLivraison || '';
        livraison.contact = data.contact || '';
        livraison.notes = data.notes || '';
        livraison.created_at = data.created_at;
        livraison.modified_at = data.modified_at;
        return livraison;
    }
}

// Export pour utilisation globale
window.Livraison = Livraison;