/**
 * DataManager - Gestion centralisée des données
 * AutoStockCheck - ECU Worldwide
 */

class DataManager {
    constructor() {
        this.commandes = [];
        this.livraisons = [];
        this.produits = [];
        this.actions = [];
        this.notifications = [];
        this.chargerDonnees();
    }

    // ==================== CHARGEMENT / SAUVEGARDE ====================
    chargerDonnees() {
        try {
            const commandesData = JSON.parse(localStorage.getItem('commandes') || '[]');
            this.commandes = commandesData.map(c => Commande.fromJSON(c));
            
            const livraisonsData = JSON.parse(localStorage.getItem('livraisons') || '[]');
            this.livraisons = livraisonsData.map(l => Livraison.fromJSON(l));
            
            const produitsData = JSON.parse(localStorage.getItem('produits') || '[]');
            this.produits = produitsData.map(p => Produit.fromJSON(p));
            
            this.actions = JSON.parse(localStorage.getItem('actions') || '[]');
            this.notifications = JSON.parse(localStorage.getItem('notifications') || '[]');
        } catch (e) {
            console.error('Erreur chargement données:', e);
        }
    }

    sauvegarderDonnees() {
        localStorage.setItem('commandes', JSON.stringify(this.commandes.map(c => c.toJSON())));
        localStorage.setItem('livraisons', JSON.stringify(this.livraisons.map(l => l.toJSON())));
        localStorage.setItem('produits', JSON.stringify(this.produits.map(p => p.toJSON())));
        localStorage.setItem('actions', JSON.stringify(this.actions));
        localStorage.setItem('notifications', JSON.stringify(this.notifications));
    }

    // ==================== COMMANDES ====================
    ajouterCommande(reference, produitRef, quantite, client, responsable, statut = 'pending', payment = 'unpaid') {
        const commande = new Commande(null, reference, produitRef, quantite, client, responsable, statut, payment);
        this.commandes.push(commande);
        this.enregistrerAction('ajout', `Commande ${reference} ajoutée`, reference, responsable);
        this.sauvegarderDonnees();
        return commande;
    }

    modifierCommande(id, updates) {
        const commande = this.commandes.find(c => c.id === id);
        if (commande) {
            Object.assign(commande, updates);
            commande.modified_at = new Date().toISOString();
            this.enregistrerAction('modification', `Commande ${commande.reference} modifiée`, commande.reference, updates.responsable);
            this.sauvegarderDonnees();
        }
        return commande;
    }

    supprimerCommande(id, raison = 'Suppression manuelle') {
        const commande = this.commandes.find(c => c.id === id);
        if (commande) {
            this.commandes = this.commandes.filter(c => c.id !== id);
            this.enregistrerAction('suppression', `Commande ${commande.reference} supprimée (${raison})`, commande.reference);
            this.sauvegarderDonnees();
            return true;
        }
        return false;
    }

    getCommandesByDate(date) {
        return this.commandes.filter(c => c.date === date);
    }

    getCommandesByResponsable(responsable) {
        return this.commandes.filter(c => c.responsable === responsable);
    }

    getCommandesByStatut(statut) {
        return this.commandes.filter(c => c.statut === statut);
    }

    // ==================== LIVRAISONS ====================
    ajouterLivraison(commandeRef, dateLivraison, heureLivraison, transporteur, chauffeur) {
        const livraison = new Livraison(null, commandeRef, dateLivraison, heureLivraison, transporteur, chauffeur);
        this.livraisons.push(livraison);
        
        const commande = this.commandes.find(c => c.reference === commandeRef);
        if (commande) commande.livrer(chauffeur);
        
        this.enregistrerAction('livraison', `Livraison planifiée pour ${commandeRef}`, commandeRef, chauffeur);
        this.sauvegarderDonnees();
        return livraison;
    }

    getLivraisonsByDate(date) {
        return this.livraisons.filter(l => l.dateLivraison === date);
    }

    getLivraisonsByChauffeur(chauffeur) {
        return this.livraisons.filter(l => l.chauffeur === chauffeur);
    }

    // ==================== PRODUITS ====================
    ajouterProduit(reference, nom, categorie, prix, stockActuel, stockMin, emplacement) {
        const produit = new Produit(null, reference, nom, categorie, prix, stockActuel, stockMin, emplacement);
        this.produits.push(produit);
        this.enregistrerAction('ajout', `Produit ${reference} (${nom}) ajouté au stock`, null);
        this.sauvegarderDonnees();
        return produit;
    }

    mettreAJourStockProduit(reference, nouvelleQuantite, raison) {
        const produit = this.produits.find(p => p.reference === reference);
        if (produit) {
            const resultat = produit.mettreAJourStock(nouvelleQuantite, raison);
            this.enregistrerAction('stock', `Stock ${reference}: ${resultat.ancien} → ${resultat.nouveau} (${raison})`, reference);
            this.sauvegarderDonnees();
            return resultat;
        }
        return null;
    }

    getProduitsStockBas() {
        return this.produits.filter(p => p.estStockBas());
    }

    // ==================== ACTIONS ====================
    enregistrerAction(type, details, commandeRef = null, responsable = null) {
        const action = {
            id: Date.now(),
            type: type,
            details: details,
            commandeRef: commandeRef,
            responsable: responsable || 'Système',
            date: new Date().toISOString(),
            lu: false
        };
        this.actions.unshift(action);
        
        if (this.actions.length > 1000) this.actions.pop();
        
        this.ajouterNotification(`📝 ${type.toUpperCase()}: ${details}`, commandeRef);
        this.sauvegarderDonnees();
        return action;
    }

    // ==================== NOTIFICATIONS ====================
    ajouterNotification(message, commandeRef = null) {
        const notification = {
            id: Date.now(),
            message: message,
            commandeRef: commandeRef,
            date: new Date().toISOString(),
            read: false
        };
        this.notifications.unshift(notification);
        
        if (this.notifications.length > 200) this.notifications.pop();
        
        this.sauvegarderDonnees();
        return notification;
    }

    getNotificationsNonLues() {
        return this.notifications.filter(n => !n.read);
    }

    marquerNotificationCommeLue(id) {
        const notif = this.notifications.find(n => n.id === id);
        if (notif) notif.read = true;
        this.sauvegarderDonnees();
    }

    // ==================== EXPORT / IMPORT ====================
    exporterDonnees() {
        return {
            commandes: this.commandes.map(c => c.toJSON()),
            livraisons: this.livraisons.map(l => l.toJSON()),
            produits: this.produits.map(p => p.toJSON()),
            actions: this.actions,
            notifications: this.notifications,
            exportDate: new Date().toISOString()
        };
    }

    importerDonnees(data) {
        this.commandes = data.commandes.map(c => Commande.fromJSON(c));
        this.livraisons = data.livraisons.map(l => Livraison.fromJSON(l));
        this.produits = data.produits.map(p => Produit.fromJSON(p));
        this.actions = data.actions;
        this.notifications = data.notifications;
        this.sauvegarderDonnees();
    }
}

// Instance globale
const dataManager = new DataManager();
window.dataManager = dataManager;