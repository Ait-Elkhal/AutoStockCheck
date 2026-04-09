/**
 * StatsRenderer - Affichage des statistiques dans le DOM
 * AutoStockCheck - ECU Worldwide
 */

class StatsRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.statsCalculator = null;
    }

    setStatsCalculator(statsCalculator) {
        this.statsCalculator = statsCalculator;
    }

    renderAll() {
        if (!this.statsCalculator || !this.container) return;
        
        const stats = this.statsCalculator.getGeneralStats();
        
        this.container.innerHTML = `
            <div class="stats-dashboard">
                ${this.renderHeader()}
                ${this.renderCommandesSection(stats.commandes)}
                ${this.renderLivraisonsSection(stats.livraisons)}
                ${this.renderStockSection(stats.stock)}
                ${this.renderActiviteSection(stats.activite)}
            </div>
        `;
    }

    renderHeader() {
        return `
            <div class="stats-header">
                <h2>📊 Tableau de bord statistique</h2>
                <div class="stats-date">Dernière mise à jour: ${new Date().toLocaleString()}</div>
            </div>
        `;
    }

    renderCommandesSection(commandesStats) {
        return `
            <div class="stats-card">
                <h3>📦 Commandes</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${commandesStats.total}</div>
                        <div class="stat-label">Total commandes</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${commandesStats.tauxValidation}%</div>
                        <div class="stat-label">Taux validation</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${commandesStats.tauxLivraison}%</div>
                        <div class="stat-label">Taux livraison</div>
                    </div>
                </div>
                <div class="stats-details">
                    <div class="stat-detail">
                        <span class="stat-detail-label">🟢 Validées:</span>
                        <span class="stat-detail-value">${commandesStats.parStatut.validated}</span>
                    </div>
                    <div class="stat-detail">
                        <span class="stat-detail-label">🟡 En attente:</span>
                        <span class="stat-detail-value">${commandesStats.parStatut.pending}</span>
                    </div>
                    <div class="stat-detail">
                        <span class="stat-detail-label">🔴 Oubliées:</span>
                        <span class="stat-detail-value">${commandesStats.parStatut.forgotten}</span>
                    </div>
                    <div class="stat-detail">
                        <span class="stat-detail-label">✅ Livrées:</span>
                        <span class="stat-detail-value">${commandesStats.parStatut.livree}</span>
                    </div>
                </div>
                <div class="stats-payment">
                    <div class="stat-detail">
                        <span class="stat-detail-label">💰 Payé:</span>
                        <span class="stat-detail-value">${commandesStats.parPaiement.paid}</span>
                    </div>
                    <div class="stat-detail">
                        <span class="stat-detail-label">💳 Non payé:</span>
                        <span class="stat-detail-value">${commandesStats.parPaiement.unpaid}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderLivraisonsSection(livraisonsStats) {
        const topChauffeurs = Object.entries(livraisonsStats.parChauffeur)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);
        
        return `
            <div class="stats-card">
                <h3>🚚 Livraisons</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${livraisonsStats.total}</div>
                        <div class="stat-label">Total livraisons</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${livraisonsStats.tauxLivraisonEffectuee}%</div>
                        <div class="stat-label">Taux effectuées</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${livraisonsStats.tauxRetard}%</div>
                        <div class="stat-label">Taux retard</div>
                    </div>
                </div>
                <div class="stats-details">
                    <div class="stat-detail">
                        <span class="stat-detail-label">📅 Planifiées:</span>
                        <span class="stat-detail-value">${livraisonsStats.parStatut.planifiee}</span>
                    </div>
                    <div class="stat-detail">
                        <span class="stat-detail-label">🚚 En cours:</span>
                        <span class="stat-detail-value">${livraisonsStats.parStatut.en_cours}</span>
                    </div>
                    <div class="stat-detail">
                        <span class="stat-detail-label">✅ Livrées:</span>
                        <span class="stat-detail-value">${livraisonsStats.parStatut.livree}</span>
                    </div>
                    <div class="stat-detail">
                        <span class="stat-detail-label">⚠️ En retard:</span>
                        <span class="stat-detail-value">${livraisonsStats.parStatut.retard}</span>
                    </div>
                </div>
                ${topChauffeurs.length > 0 ? `
                    <div class="stats-top-list">
                        <div class="stats-top-title">🏆 Top chauffeurs</div>
                        ${topChauffeurs.map(([nom, nb]) => `
                            <div class="stat-detail">
                                <span class="stat-detail-label">${nom}:</span>
                                <span class="stat-detail-value">${nb} livraisons</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderStockSection(stockStats) {
        const produitsCritiques = stockStats.listeProduitsStockBas.slice(0, 5);
        
        return `
            <div class="stats-card">
                <h3>🏭 Stock</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${stockStats.totalProduits}</div>
                        <div class="stat-label">Produits</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stockStats.produitsStockBas}</div>
                        <div class="stat-label">Stock bas</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${Math.round(stockStats.valeurTotaleStock).toLocaleString()} €</div>
                        <div class="stat-label">Valeur stock</div>
                    </div>
                </div>
                ${produitsCritiques.length > 0 ? `
                    <div class="stats-alert">
                        <div class="stats-alert-title">⚠️ Alertes stock bas</div>
                        ${produitsCritiques.map(p => `
                            <div class="stat-detail">
                                <span class="stat-detail-label">${p.reference} - ${p.nom}:</span>
                                <span class="stat-detail-value">${p.stock} / ${p.stockMin} min</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderActiviteSection(activiteStats) {
        const topResponsables = Object.entries(activiteStats.commandesParResponsable)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);
        
        return `
            <div class="stats-card">
                <h3>📋 Activité</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${activiteStats.totalActions}</div>
                        <div class="stat-label">Actions enregistrées</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${activiteStats.notificationsNonLues}</div>
                        <div class="stat-label">Notifications</div>
                    </div>
                </div>
                ${topResponsables.length > 0 ? `
                    <div class="stats-top-list">
                        <div class="stats-top-title">👥 Top responsables</div>
                        ${topResponsables.map(([nom, nb]) => `
                            <div class="stat-detail">
                                <span class="stat-detail-label">${nom}:</span>
                                <span class="stat-detail-value">${nb} commandes</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderEvolution(evolution) {
        if (!this.container) return;
        
        const evolutionHtml = `
            <div class="stats-card evolution-card">
                <h3>📈 Évolution des commandes (30 jours)</h3>
                <div class="evolution-chart" id="evolutionChart"></div>
                <div class="evolution-data">
                    ${evolution.slice(-7).map(e => `
                        <div class="evolution-day">
                            <div class="evolution-date">${e.date}</div>
                            <div class="evolution-count">${e.commandes} commandes</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        this.container.innerHTML += evolutionHtml;
    }
}

window.StatsRenderer = StatsRenderer;