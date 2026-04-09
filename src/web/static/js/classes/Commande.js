/**
 * Classe Commande - Gestion des commandes clients
 * AutoStockCheck - ECU Worldwide
 */

class Commande {
    constructor(id, reference, produitRef, quantite, client, responsable, statut = 'pending', payment = 'unpaid') {
        this.id = id || Date.now();
        this.reference = reference;
        this.produitRef = produitRef;
        this.quantite = quantite || 1;
        this.client = client || 'Client non spécifié';
        this.responsable = responsable || 'Non assigné';
        this.statut = statut; // 'pending', 'validated', 'forgotten', 'livree'
        this.payment = payment; // 'paid', 'unpaid'
        this.date = new Date().toISOString().split('T')[0];
        this.heure = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        this.description = '';
        this.created_at = new Date().toISOString();
        this.modified_at = new Date().toISOString();
        this.actions = []; // Historique des actions sur cette commande
    }

    // Ajouter une action à l'historique de la commande
    ajouterAction(type, details, utilisateur) {
        const action = {
            id: Date.now(),
            type: type,
            details: details,
            utilisateur: utilisateur,
            date: new Date().toISOString()
        };
        this.actions.push(action);
        this.modified_at = new Date().toISOString();
        return action;
    }

    // Changer le statut
    changerStatut(nouveauStatut, utilisateur) {
        const ancienStatut = this.statut;
        this.statut = nouveauStatut;
        this.ajouterAction('statut', `Statut changé: ${ancienStatut} → ${nouveauStatut}`, utilisateur);
        return { ancien: ancienStatut, nouveau: nouveauStatut };
    }

    // Changer le paiement
    changerPaiement(nouveauPaiement, utilisateur) {
        const ancienPaiement = this.payment;
        this.payment = nouveauPaiement;
        this.ajouterAction('paiement', `Paiement changé: ${ancienPaiement} → ${nouveauPaiement}`, utilisateur);
        return { ancien: ancienPaiement, nouveau: nouveauPaiement };
    }

    // Valider la commande
    valider(utilisateur) {
        return this.changerStatut('validated', utilisateur);
    }

    // Marquer comme livrée
    livrer(utilisateur) {
        return this.changerStatut('livree', utilisateur);
    }

    // Marquer comme oubliée
    oublier(utilisateur) {
        return this.changerStatut('forgotten', utilisateur);
    }

    // Obtenir le libellé du statut
    getStatutLabel() {
        const labels = {
            'pending': '🟡 En attente',
            'validated': '🟢 Validée',
            'forgotten': '🔴 Oubliée',
            'livree': '✅ Livrée'
        };
        return labels[this.statut] || this.statut;
    }

    // Obtenir le libellé du paiement
    getPaymentLabel() {
        return this.payment === 'paid' ? '💰 Payé' : '💳 Non payé';
    }

    // Convertir en objet JSON
    toJSON() {
        return {
            id: this.id,
            reference: this.reference,
            produitRef: this.produitRef,
            quantite: this.quantite,
            client: this.client,
            responsable: this.responsable,
            statut: this.statut,
            payment: this.payment,
            date: this.date,
            heure: this.heure,
            description: this.description,
            created_at: this.created_at,
            modified_at: this.modified_at,
            actions: this.actions
        };
    }

    // Créer une commande depuis un objet
    static fromJSON(data) {
        const commande = new Commande(
            data.id,
            data.reference,
            data.produitRef,
            data.quantite,
            data.client,
            data.responsable,
            data.statut,
            data.payment
        );
        commande.date = data.date;
        commande.heure = data.heure;
        commande.description = data.description || '';
        commande.created_at = data.created_at;
        commande.modified_at = data.modified_at;
        commande.actions = data.actions || [];
        return commande;
    }
}

// Export pour utilisation globale
window.Commande = Commande;