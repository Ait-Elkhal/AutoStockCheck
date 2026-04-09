/**
 * StatsCharts - Création de graphiques pour les statistiques
 * AutoStockCheck - ECU Worldwide
 */

class StatsCharts {
    constructor() {
        this.charts = {};
    }

    // Créer un graphique en barres
    createBarChart(canvasId, labels, data, title, colors = ['#4361ee']) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: title,
                    data: data,
                    backgroundColor: colors[0],
                    borderColor: colors[0],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }

    // Créer un graphique en camembert
    createPieChart(canvasId, labels, data, title) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        const colors = ['#4caf50', '#ffc107', '#f44336', '#2196f3', '#9c27b0'];
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, data.length),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: title }
                }
            }
        });
        
        return this.charts[canvasId];
    }

    // Créer un graphique linéaire pour l'évolution
    createLineChart(canvasId, labels, datasets, title) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: title }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        return this.charts[canvasId];
    }

    // Créer un graphique d'évolution des commandes
    renderCommandesEvolution(evolution) {
        const canvasId = 'evolutionCommandesChart';
        const labels = evolution.map(e => e.date.substring(5));
        const datasets = [
            {
                label: 'Commandes',
                data: evolution.map(e => e.commandes),
                borderColor: '#4361ee',
                backgroundColor: 'rgba(67, 97, 238, 0.1)',
                fill: true,
                tension: 0.3
            },
            {
                label: 'Livrées',
                data: evolution.map(e => e.livrees),
                borderColor: '#4caf50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                fill: true,
                tension: 0.3
            }
        ];
        
        return this.createLineChart(canvasId, labels, datasets, 'Évolution des commandes (30 jours)');
    }

    // Créer un graphique de répartition des statuts
    renderStatutsRepartition(stats) {
        const canvasId = 'statutsRepartitionChart';
        const labels = ['Validées', 'En attente', 'Oubliées', 'Livrées'];
        const data = [
            stats.commandes.parStatut.validated,
            stats.commandes.parStatut.pending,
            stats.commandes.parStatut.forgotten,
            stats.commandes.parStatut.livree
        ];
        
        return this.createPieChart(canvasId, labels, data, 'Répartition des commandes');
    }

    // Créer un graphique de répartition des paiements
    renderPaiementsRepartition(stats) {
        const canvasId = 'paiementsRepartitionChart';
        const labels = ['Payé', 'Non payé'];
        const data = [
            stats.commandes.parPaiement.paid,
            stats.commandes.parPaiement.unpaid
        ];
        
        return this.createPieChart(canvasId, labels, data, 'Répartition des paiements');
    }

    // Créer un graphique des livraisons par statut
    renderLivraisonsStatuts(stats) {
        const canvasId = 'livraisonsStatutsChart';
        const labels = ['Planifiées', 'En cours', 'Livrées', 'En retard', 'Annulées'];
        const data = [
            stats.livraisons.parStatut.planifiee,
            stats.livraisons.parStatut.en_cours,
            stats.livraisons.parStatut.livree,
            stats.livraisons.parStatut.retard,
            stats.livraisons.parStatut.annulee
        ];
        
        return this.createPieChart(canvasId, labels, data, 'Répartition des livraisons');
    }

    // Créer un graphique des produits par catégorie
    renderProduitsParCategorie(stockStats) {
        const canvasId = 'produitsParCategorieChart';
        const categories = Object.keys(stockStats.parCategorie);
        const quantites = categories.map(c => stockStats.parCategorie[c]);
        
        return this.createBarChart(canvasId, categories, quantites, 'Produits par catégorie', ['#4361ee']);
    }

    // Créer un graphique des top responsables
    renderTopResponsables(activiteStats) {
        const canvasId = 'topResponsablesChart';
        const responsables = Object.keys(activiteStats.commandesParResponsable).slice(0, 10);
        const commandes = responsables.map(r => activiteStats.commandesParResponsable[r]);
        
        return this.createBarChart(canvasId, responsables, commandes, 'Top responsables (commandes)', ['#4caf50']);
    }

    // Détruire tous les graphiques
    destroyAll() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) chart.destroy();
        });
        this.charts = {};
    }
}

window.StatsCharts = StatsCharts;