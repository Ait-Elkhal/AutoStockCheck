/**
 * StatsCalculator - Calcul des statistiques
 * AutoStockCheck - ECU Worldwide
 */

class StatsCalculator {
    constructor(dataManager) {
        this.dataManager = dataManager;
    }

    // Statistiques des commandes
    getCommandesStats() {
        const commandes = this.dataManager.commandes;
        const total = commandes.length;
        
        const parStatut = {
            pending: commandes.filter(c => c.statut === 'pending').length,
            validated: commandes.filter(c => c.statut === 'validated').length,
            forgotten: commandes.filter(c => c.statut === 'forgotten').length,
            livree: commandes.filter(c => c.statut === 'livree').length
        };
        
        const parPaiement = {
            paid: commandes.filter(c => c.payment === 'paid').length,
            unpaid: commandes.filter(c => c.payment === 'unpaid').length
        };
        
        // Tendance sur les 7 derniers jours
        const tendance = this.getTendanceCommandes(7);
        
        return {
            total,
            parStatut,
            parPaiement,
            tauxValidation: total > 0 ? (parStatut.validated / total * 100).toFixed(1) : 0,
            tauxLivraison: total > 0 ? (parStatut.livree / total * 100).toFixed(1) : 0,
            tendance
        };
    }

    getTendanceCommandes(jours = 7) {
        const resultats = [];
        const today = new Date();
        
        for (let i = jours - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(today.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            const commandesJour = this.dataManager.commandes.filter(c => c.date === dateStr);
            resultats.push({
                date: dateStr,
                total: commandesJour.length,
                validees: commandesJour.filter(c => c.statut === 'validated').length,
                livrees: commandesJour.filter(c => c.statut === 'livree').length
            });
        }
        
        return resultats;
    }

    // Statistiques des livraisons
    getLivraisonsStats() {
        const livraisons = this.dataManager.livraisons;
        const total = livraisons.length;
        
        const parStatut = {
            planifiee: livraisons.filter(l => l.statut === 'planifiee').length,
            en_cours: livraisons.filter(l => l.statut === 'en_cours').length,
            livree: livraisons.filter(l => l.statut === 'livree').length,
            retard: livraisons.filter(l => l.statut === 'retard').length,
            annulee: livraisons.filter(l => l.statut === 'annulee').length
        };
        
        const parChauffeur = {};
        livraisons.forEach(l => {
            if (l.chauffeur && l.chauffeur !== 'Non assigné') {
                parChauffeur[l.chauffeur] = (parChauffeur[l.chauffeur] || 0) + 1;
            }
        });
        
        const parTransporteur = {};
        livraisons.forEach(l => {
            if (l.transporteur && l.transporteur !== 'À définir') {
                parTransporteur[l.transporteur] = (parTransporteur[l.transporteur] || 0) + 1;
            }
        });
        
        return {
            total,
            parStatut,
            parChauffeur,
            parTransporteur,
            tauxLivraisonEffectuee: total > 0 ? (parStatut.livree / total * 100).toFixed(1) : 0,
            tauxRetard: total > 0 ? (parStatut.retard / total * 100).toFixed(1) : 0
        };
    }

    // Statistiques des stocks
    getStockStats() {
        const produits = this.dataManager.produits;
        const totalProduits = produits.length;
        
        const parCategorie = {};
        produits.forEach(p => {
            parCategorie[p.categorie] = (parCategorie[p.categorie] || 0) + 1;
        });
        
        const produitsStockBas = produits.filter(p => p.estStockBas());
        const valeurTotaleStock = produits.reduce((sum, p) => sum + p.valeurStock(), 0);
        
        return {
            totalProduits,
            parCategorie,
            produitsStockBas: produitsStockBas.length,
            listeProduitsStockBas: produitsStockBas.map(p => ({ reference: p.reference, nom: p.nom, stock: p.stockActuel, stockMin: p.stockMin })),
            valeurTotaleStock,
            valeurMoyenneParProduit: totalProduits > 0 ? valeurTotaleStock / totalProduits : 0
        };
    }

    // Statistiques générales
    getGeneralStats() {
        const commandesStats = this.getCommandesStats();
        const livraisonsStats = this.getLivraisonsStats();
        const stockStats = this.getStockStats();
        
        const totalActions = this.dataManager.actions.length;
        const notificationsNonLues = this.dataManager.getNotificationsNonLues().length;
        
        // Commandes par responsable
        const commandesParResponsable = {};
        this.dataManager.commandes.forEach(c => {
            if (c.responsable && c.responsable !== 'Non assigné') {
                commandesParResponsable[c.responsable] = (commandesParResponsable[c.responsable] || 0) + 1;
            }
        });
        
        return {
            commandes: commandesStats,
            livraisons: livraisonsStats,
            stock: stockStats,
            activite: {
                totalActions,
                notificationsNonLues,
                commandesParResponsable
            },
            dateCalcul: new Date().toISOString()
        };
    }

    // Évolution dans le temps
    getEvolution(periodes = 30) {
        const evolution = [];
        const today = new Date();
        
        for (let i = periodes - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(today.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            const commandesJour = this.dataManager.commandes.filter(c => c.date === dateStr);
            const livraisonsJour = this.dataManager.livraisons.filter(l => l.dateLivraison === dateStr);
            
            evolution.push({
                date: dateStr,
                commandes: commandesJour.length,
                livraisons: livraisonsJour.length,
                valeurCommandes: commandesJour.reduce((sum, c) => sum + (c.quantite * (c.produitRef ? 100 : 0)), 0)
            });
        }
        
        return evolution;
    }
}

window.StatsCalculator = StatsCalculator;