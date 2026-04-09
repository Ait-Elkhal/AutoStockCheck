// AutoStockCheck - JavaScript principal
const API_URL = 'http://localhost:5000';

let historique = [];
let evolutionChart = null;
let performanceChart = null;

// Navigation entre onglets
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    document.getElementById(tabId).style.display = 'block';
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    if (tabId === 'historique') {
        chargerHistorique();
    } else if (tabId === 'stats') {
        chargerStatistiques();
    }
}

// Vérification d'une commande
async function verifier() {
    const data = {
        facture: {
            quantite: parseInt(document.getElementById('qte_facture').value) || 0,
            prix: parseFloat(document.getElementById('prix').value) || 0,
            popularite: parseFloat(document.getElementById('popularite').value) || 0.6
        },
        stock: {
            quantite: parseInt(document.getElementById('qte_stock').value) || 0,
            etat_produit: parseFloat(document.getElementById('etat_produit').value) || 0.95
        },
        reference: document.getElementById('reference').value || 'UNKNOWN',
        produit: document.getElementById('produit').value || 'Produit',
        client_email: document.getElementById('client_email').value || 'client@test.com'
    };
    
    document.getElementById('loading').style.display = 'block';
    document.getElementById('resultat').style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        afficherResultat(result, data);
        sauvegarderHistorique(result, data);
        
    } catch (error) {
        console.error('Erreur:', error);
        afficherErreur(error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Affichage du résultat
function afficherResultat(result, data) {
    const isManque = result.prediction === 1;
    const resultDiv = document.getElementById('resultat');
    
    resultDiv.innerHTML = `
        <div class="result-card ${isManque ? 'result-warning' : 'result-success'}">
            <div class="result-title">
                ${isManque ? '⚠️ MANQUE DÉTECTÉ' : '✅ COMMANDE CONFORME'}
            </div>
            <div class="result-probability">
                Probabilité de manque: ${(result.probabilite_manque * 100).toFixed(1)}%
            </div>
            <div style="margin-top: 20px;">
                <strong>📋 Détails:</strong><br>
                Référence: ${data.reference}<br>
                Produit: ${data.produit}<br>
                Quantité commandée: ${data.facture.quantite}<br>
                Quantité en stock: ${data.stock.quantite}<br>
                Différence: ${data.facture.quantite - data.stock.quantite}
            </div>
            <div style="margin-top: 20px;">
                <strong>🔬 Features extraites:</strong>
                <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px;">
                    ${Object.entries(result.features).slice(0, 8).map(([k, v]) => 
                        `<span class="badge badge-warning">${k}: ${v.toFixed(3)}</span>`
                    ).join('')}
                </div>
            </div>
            <div style="margin-top: 20px;">
                <button class="btn btn-primary" onclick="verifier()">🔄 Nouvelle vérification</button>
                <button class="btn" style="margin-left: 10px;" onclick="envoyerRapport()">📧 Envoyer rapport</button>
            </div>
        </div>
    `;
    
    resultDiv.style.display = 'block';
}

// Charger l'historique
async function chargerHistorique() {
    try {
        const response = await fetch(`${API_URL}/history`);
        const data = await response.json();
        historique = data.historique || [];
        afficherHistorique();
    } catch (error) {
        console.error('Erreur chargement historique:', error);
        afficherHistoriqueDemo();
    }
}

// Affichage de l'historique
function afficherHistorique() {
    const container = document.getElementById('historique-list');
    
    if (historique.length === 0) {
        container.innerHTML = '<p>Aucune vérification enregistrée.</p>';
        return;
    }
    
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Référence</th>
                    <th>Produit</th>
                    <th>Quantité</th>
                    <th>Stock</th>
                    <th>Résultat</th>
                    <th>Probabilité</th>
                </tr>
            </thead>
            <tbody>
                ${historique.slice(0, 20).map(item => `
                    <tr>
                        <td>${new Date(item.date).toLocaleString()}</td>
                        <td>${item.reference}</td>
                        <td>${item.produit}</td>
                        <td>${item.quantite_facture}</td>
                        <td>${item.quantite_stock}</td>
                        <td>
                            <span class="badge ${item.prediction === 1 ? 'badge-danger' : 'badge-success'}">
                                ${item.prediction === 1 ? 'Manque' : 'Conforme'}
                            </span>
                        </td>
                        <td>${(item.probabilite * 100).toFixed(1)}%</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Charger les statistiques
async function chargerStatistiques() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const stats = await response.json();
        
        document.getElementById('stat-total').textContent = stats.total || 0;
        document.getElementById('stat-conformes').textContent = stats.conformes || 0;
        document.getElementById('stat-manques').textContent = stats.manques || 0;
        document.getElementById('stat-taux').textContent = `${(stats.taux || 0).toFixed(1)}%`;
        
        // Graphique d'évolution
        if (evolutionChart) evolutionChart.destroy();
        const ctx = document.getElementById('evolution-chart').getContext('2d');
        evolutionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: stats.jours || ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
                datasets: [{
                    label: 'Commandes traitées',
                    data: stats.evolution || [0, 0, 0, 0, 0, 0, 0],
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: { responsive: true, maintainAspectRatio: true }
        });
        
        // Graphique de performance
        if (performanceChart) performanceChart.destroy();
        const ctx2 = document.getElementById('performance-chart').getContext('2d');
        performanceChart = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: ['Decision Tree', 'SVM', 'Random Forest', 'Neural Network'],
                datasets: [{
                    label: 'F1-Score',
                    data: stats.performances || [0.86, 1.0, 0.91, 1.0],
                    backgroundColor: ['#4361ee', '#7209b7', '#06ffa5', '#ef476f']
                }]
            },
            options: { responsive: true, maintainAspectRatio: true }
        });
        
    } catch (error) {
        console.error('Erreur chargement stats:', error);
        chargerStatistiquesDemo();
    }
}

// Sauvegarder la configuration
function sauvegarderConfig() {
    const config = {
        email_reception: document.getElementById('config_email_reception').value,
        email_stock: document.getElementById('config_email_stock').value,
        modele: document.getElementById('config_modele').value,
        seuil: parseFloat(document.getElementById('config_seuil').value)
    };
    
    localStorage.setItem('autostockcheck_config', JSON.stringify(config));
    alert('✅ Configuration sauvegardée !');
}

// Sauvegarder les templates
function sauvegarderTemplates() {
    const templates = {
        conforme: document.getElementById('template_conforme').value,
        manque: document.getElementById('template_manque').value
    };
    
    localStorage.setItem('autostockcheck_templates', JSON.stringify(templates));
    alert('✅ Templates sauvegardés !');
}

// Charger la configuration sauvegardée
function chargerConfig() {
    const saved = localStorage.getItem('autostockcheck_config');
    if (saved) {
        const config = JSON.parse(saved);
        if (document.getElementById('config_email_reception')) {
            document.getElementById('config_email_reception').value = config.email_reception;
            document.getElementById('config_email_stock').value = config.email_stock;
            document.getElementById('config_modele').value = config.modele;
            document.getElementById('config_seuil').value = config.seuil;
        }
    }
    
    const savedTemplates = localStorage.getItem('autostockcheck_templates');
    if (savedTemplates) {
        const templates = JSON.parse(savedTemplates);
        if (document.getElementById('template_conforme')) {
            document.getElementById('template_conforme').value = templates.conforme;
            document.getElementById('template_manque').value = templates.manque;
        }
    }
}

// Sauvegarder l'historique localement
function sauvegarderHistorique(result, data) {
    const item = {
        date: new Date().toISOString(),
        reference: data.reference,
        produit: data.produit,
        quantite_facture: data.facture.quantite,
        quantite_stock: data.stock.quantite,
        prediction: result.prediction,
        probabilite: result.probabilite_manque
    };
    
    let historique = JSON.parse(localStorage.getItem('autostockcheck_historique') || '[]');
    historique.unshift(item);
    historique = historique.slice(0, 100);
    localStorage.setItem('autostockcheck_historique', JSON.stringify(historique));
}

// Charger l'historique local
function afficherHistoriqueDemo() {
    const historique = JSON.parse(localStorage.getItem('autostockcheck_historique') || '[]');
    const container = document.getElementById('historique-list');
    
    if (historique.length === 0) {
        container.innerHTML = '<p>Aucune vérification enregistrée. Effectuez des tests dans l\'onglet "Vérification".</p>';
        return;
    }
    
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Référence</th>
                    <th>Produit</th>
                    <th>Quantité</th>
                    <th>Stock</th>
                    <th>Résultat</th>
                    <th>Probabilité</th>
                </tr>
            </thead>
            <tbody>
                ${historique.slice(0, 20).map(item => `
                    <tr>
                        <td>${new Date(item.date).toLocaleString()}</td>
                        <td>${item.reference}</td>
                        <td>${item.produit}</td>
                        <td>${item.quantite_facture}</td>
                        <td>${item.quantite_stock}</td>
                        <td>
                            <span class="badge ${item.prediction === 1 ? 'badge-danger' : 'badge-success'}">
                                ${item.prediction === 1 ? 'Manque' : 'Conforme'}
                            </span>
                        </td>
                        <td>${(item.probabilite * 100).toFixed(1)}%</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Statistiques démo
function chargerStatistiquesDemo() {
    document.getElementById('stat-total').textContent = historique.length;
    const manques = historique.filter(h => h.prediction === 1).length;
    document.getElementById('stat-manques').textContent = manques;
    document.getElementById('stat-conformes').textContent = historique.length - manques;
    document.getElementById('stat-taux').textContent = historique.length > 0 ? `${(manques / historique.length * 100).toFixed(1)}%` : '0%';
}

// Erreur
function afficherErreur(message) {
    const resultDiv = document.getElementById('resultat');
    resultDiv.innerHTML = `
        <div class="result-card result-warning">
            <div class="result-title">❌ Erreur</div>
            <p>${message}</p>
            <p>Vérifiez que l'API est démarrée (python src/api/app.py)</p>
            <button class="btn btn-primary" onclick="verifier()">🔄 Réessayer</button>
        </div>
    `;
    resultDiv.style.display = 'block';
}

// Envoyer rapport par email (simulation)
function envoyerRapport() {
    alert('📧 Rapport envoyé par email (simulation)\n\nDans la version finale, l\'email serait envoyé automatiquement via n8n.');
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    chargerConfig();
    chargerHistorique();
});
// ==================== BARRE DE MENU DYNAMIQUE ====================
let lastScrollTop = 0;
const navbar = document.getElementById('navbar');
const scrollTopBtn = document.getElementById('scrollTopBtn');

// Fonction pour gérer la barre de menu
function handleNavbarScroll() {
    const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
    
    if (currentScroll > lastScrollTop && currentScroll > 100) {
        // Scroll vers le bas - cacher la barre
        navbar.classList.add('hide');
        navbar.classList.remove('show');
    } else {
        // Scroll vers le haut - montrer la barre
        navbar.classList.remove('hide');
        navbar.classList.add('show');
    }
    
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
}

// Fonction pour gérer l'affichage du bouton scroll to top
function handleScrollTopButton() {
    const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
    
    if (currentScroll > 300) {
        scrollTopBtn.classList.add('show');
    } else {
        scrollTopBtn.classList.remove('show');
    }
}

// Fonction pour remonter en haut
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Écouteurs d'événements
window.addEventListener('scroll', function() {
    handleNavbarScroll();
    handleScrollTopButton();
});

// Au chargement de la page, initialiser
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser la barre de menu
    navbar.classList.add('show');
    
    // Ajouter l'écouteur pour le bouton scroll to top
    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', scrollToTop);
    }
    
    // Gérer le cas où la page est déjà scrollée
    handleScrollTopButton();
});