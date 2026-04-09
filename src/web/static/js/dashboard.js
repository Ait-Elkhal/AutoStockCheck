// AutoStockCheck - Dashboard JavaScript
const API_URL = 'http://localhost:5000';

let historique = [];
let evolutionChart = null;
let performanceChart = null;
let currentUser = null;

// ==================== INITIALISATION ====================

document.addEventListener('DOMContentLoaded', () => {
    // Vérifier l'authentification
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    currentUser = JSON.parse(localStorage.getItem('user') || '{}');
    document.getElementById('userName').textContent = currentUser.username || 'Utilisateur';
    
    chargerConfig();
    chargerHistorique();
    chargerEmails();
    chargerRapports();
});

// ==================== NAVIGATION ====================

function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
    document.getElementById(tabId).style.display = 'block';
    
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    if (tabId === 'historique') chargerHistorique();
    else if (tabId === 'emails') chargerEmails();
    else if (tabId === 'rapports') chargerRapports();
    else if (tabId === 'stats') chargerStatistiques();
}

// ==================== AUTHENTIFICATION ====================

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// ==================== VÉRIFICATION ====================

async function verifier() {
    const data = {
        facture: {
            quantite: parseInt(document.getElementById('qte_facture').value) || 0,
            prix: parseFloat(document.getElementById('prix').value) || 0,
            popularite: 0.6
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
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        afficherResultat(result, data);
        chargerHistorique();
        chargerStatistiques();
        
    } catch (error) {
        console.error('Erreur:', error);
        afficherErreur(error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function afficherResultat(result, data) {
    const isManque = result.prediction === 1;
    const resultDiv = document.getElementById('resultat');
    
    resultDiv.innerHTML = `
        <div class="result-card ${isManque ? 'result-warning' : 'result-success'}">
            <div class="result-title">${isManque ? '⚠️ MANQUE DÉTECTÉ' : '✅ COMMANDE CONFORME'}</div>
            <div class="result-probability">Probabilité de manque: ${(result.probabilite_manque * 100).toFixed(1)}%</div>
            <div><strong>📋 Détails:</strong><br>Référence: ${data.reference}<br>Produit: ${data.produit}<br>Quantité commandée: ${data.facture.quantite}<br>Quantité en stock: ${data.stock.quantite}<br>Différence: ${data.facture.quantite - data.stock.quantite}</div>
            <div style="margin-top: 20px;"><button class="btn btn-primary" onclick="verifier()">🔄 Nouvelle vérification</button></div>
        </div>
    `;
    resultDiv.style.display = 'block';
}

// ==================== HISTORIQUE ====================

async function chargerHistorique() {
    try {
        const response = await fetch(`${API_URL}/history`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await response.json();
        historique = data.historique || [];
        afficherHistorique();
    } catch (error) {
        afficherHistoriqueLocal();
    }
}

function afficherHistorique() {
    const container = document.getElementById('historique-list');
    if (!historique.length) { container.innerHTML = '<p>Aucune vérification enregistrée.</p>'; return; }
    
    container.innerHTML = `
        <table class="table"><thead><tr><th>Date</th><th>Réf.</th><th>Produit</th><th>Qté</th><th>Stock</th><th>Résultat</th><th>Probabilité</th><th>Email</th></tr></thead><tbody>
            ${historique.map(item => `<tr>
                <td>${new Date(item.date).toLocaleString()}</td>
                <td>${item.reference}</td><td>${item.produit}</td>
                <td>${item.quantite_facture}</td><td>${item.quantite_stock}</td>
                <td><span class="badge ${item.prediction === 1 ? 'badge-danger' : 'badge-success'}">${item.prediction === 1 ? 'Manque' : 'Conforme'}</span></td>
                <td>${(item.probabilite * 100).toFixed(1)}%</td>
                <td>${item.client_email || '-'}</td>
            </tr>`).join('')}
        </tbody></table>
    `;
}

// ==================== EMAILS ====================

async function chargerEmails() {
    try {
        const response = await fetch(`${API_URL}/emails`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await response.json();
        afficherEmails(data);
    } catch (error) {
        afficherEmailsDemo();
    }
}

function afficherEmails(data) {
    const recusDiv = document.getElementById('emails-recus');
    const envoyesDiv = document.getElementById('emails-envoyes');
    
    recusDiv.innerHTML = `<table class="table"><thead><tr><th>Date</th><th>Expéditeur</th><th>Objet</th><th>Statut</th></tr></thead><tbody>
        ${(data.recus || []).map(e => `<tr><td>${new Date(e.date).toLocaleString()}</td><td>${e.expediteur}</td><td>${e.objet}</td><td>${e.statut}</td></tr>`).join('')}
    </tbody></table>`;
    
    envoyesDiv.innerHTML = `<table class="table"><thead><tr><th>Date</th><th>Destinataire</th><th>Objet</th><th>Statut</th></tr></thead><tbody>
        ${(data.envoyes || []).map(e => `<tr><td>${new Date(e.date).toLocaleString()}</td><td>${e.destinataire}</td><td>${e.objet}</td><td>${e.statut}</td></tr>`).join('')}
    </tbody></table>`;
}

async function envoyerEmail() {
    const data = {
        destinataire: document.getElementById('email_destinataire').value,
        objet: document.getElementById('email_objet').value,
        message: document.getElementById('email_message').value
    };
    
    const response = await fetch(`${API_URL}/send-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify(data)
    });
    
    if (response.ok) {
        alert('✅ Email envoyé !');
        document.getElementById('email_destinataire').value = '';
        document.getElementById('email_objet').value = '';
        document.getElementById('email_message').value = '';
        chargerEmails();
    } else {
        alert('❌ Erreur lors de l\'envoi');
    }
}

// ==================== RAPPORTS ====================

async function chargerRapports() {
    try {
        const response = await fetch(`${API_URL}/reports`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await response.json();
        afficherRapports(data.rapports || []);
    } catch (error) {
        afficherRapportsDemo();
    }
}

function afficherRapports(rapports) {
    const container = document.getElementById('rapports-list');
    container.innerHTML = `
        <table class="table"><thead><tr><th>Date</th><th>Type</th><th>Commande</th><th>Statut</th><th>Actions</th></tr></thead><tbody>
            ${rapports.map(r => `<tr>
                <td>${new Date(r.date).toLocaleString()}</td>
                <td>${r.type}</td>
                <td>${r.reference}</td>
                <td><span class="badge ${r.prediction === 1 ? 'badge-danger' : 'badge-success'}">${r.prediction === 1 ? 'Manque' : 'Conforme'}</span></td>
                <td><button class="btn" onclick="telechargerRapport('${r.id}')">📄 Voir</button></td>
            </tr>`).join('')}
        </tbody></table>
    `;
}

function genererRapport() {
    alert('📊 Génération du rapport mensuel...\n\nLe rapport sera envoyé par email sous 24h.');
}

// ==================== STATISTIQUES ====================

async function chargerStatistiques() {
    try {
        const response = await fetch(`${API_URL}/stats`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const stats = await response.json();
        
        document.getElementById('stat-total').textContent = stats.total || 0;
        document.getElementById('stat-conformes').textContent = stats.conformes || 0;
        document.getElementById('stat-manques').textContent = stats.manques || 0;
        document.getElementById('stat-taux').textContent = `${(stats.taux || 0).toFixed(1)}%`;
        
        if (evolutionChart) evolutionChart.destroy();
        const ctx = document.getElementById('evolution-chart').getContext('2d');
        evolutionChart = new Chart(ctx, {
            type: 'line',
            data: { labels: stats.jours || ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'], datasets: [{ label: 'Commandes', data: stats.evolution || [0,0,0,0,0,0,0], borderColor: '#4361ee', tension: 0.3, fill: true }] },
            options: { responsive: true }
        });
        
        if (performanceChart) performanceChart.destroy();
        const ctx2 = document.getElementById('performance-chart').getContext('2d');
        performanceChart = new Chart(ctx2, {
            type: 'bar',
            data: { labels: ['Decision Tree', 'SVM', 'Random Forest', 'Neural Network'], datasets: [{ label: 'F1-Score', data: stats.performances || [0.86, 1.0, 0.91, 1.0], backgroundColor: ['#4361ee', '#7209b7', '#06ffa5', '#ef476f'] }] },
            options: { responsive: true }
        });
    } catch (error) {
        console.error('Erreur stats:', error);
    }
}

// ==================== CONFIGURATION ====================

function chargerConfig() {
    const saved = JSON.parse(localStorage.getItem('autostockcheck_config') || '{}');
    document.getElementById('config_company').value = saved.company || currentUser.company || '';
    document.getElementById('config_storage').value = saved.storage_type || '';
    document.getElementById('config_email_stock').value = saved.email_stock || '';
    document.getElementById('config_email_notif').value = saved.email_notification || '';
    document.getElementById('template_conforme').value = saved.template_conforme || 'Bonjour {client_nom},\n\nVotre commande {reference} est conforme.\nCordialement, ECU Worldwide';
    document.getElementById('template_manque').value = saved.template_manque || 'Bonjour {client_nom},\n\nUn manque a été détecté sur votre commande {reference}.\nNous vous contacterons sous 24h.\nCordialement, ECU Worldwide';
}

function sauvegarderConfig() {
    const config = {
        company: document.getElementById('config_company').value,
        storage_type: document.getElementById('config_storage').value,
        email_stock: document.getElementById('config_email_stock').value,
        email_notification: document.getElementById('config_email_notif').value,
        template_conforme: document.getElementById('template_conforme').value,
        template_manque: document.getElementById('template_manque').value
    };
    localStorage.setItem('autostockcheck_config', JSON.stringify(config));
    alert('✅ Configuration sauvegardée !');
}

function sauvegarderTemplates() { sauvegarderConfig(); }

// ==================== FONCTIONS SECONDAIRES ====================

function afficherHistoriqueLocal() { afficherHistorique(); }
function afficherEmailsDemo() { document.getElementById('emails-recus').innerHTML = '<p>Aucun email pour le moment.</p>'; document.getElementById('emails-envoyes').innerHTML = '<p>Aucun email pour le moment.</p>'; }
function afficherRapportsDemo() { document.getElementById('rapports-list').innerHTML = '<p>Aucun rapport généré.</p>'; }
function afficherErreur(msg) { const d = document.getElementById('resultat'); d.innerHTML = `<div class="result-card result-warning"><div class="result-title">❌ Erreur</div><p>${msg}</p></div>`; d.style.display = 'block'; }
function telechargerRapport(id) { alert(`📄 Téléchargement du rapport ${id}`); }

// Stockage local
let stockItems = JSON.parse(localStorage.getItem('stockItems') || '[]');
let livraisons = JSON.parse(localStorage.getItem('livraisons') || '[]');
let users = JSON.parse(localStorage.getItem('users') || '[]');

// Gestion du stock
function afficherStock() {
    const container = document.getElementById('stock-list');
    if (!container) return;
    
    if (stockItems.length === 0) {
        container.innerHTML = '<p>Aucun produit en stock.</p>';
        return;
    }
    
    container.innerHTML = stockItems.map(item => `
        <div class="stock-item">
            <div class="stock-info">
                <h4>${item.nom}</h4>
                <p>Réf: ${item.reference}</p>
                <p>Emplacement: ${item.emplacement}</p>
            </div>
            <div class="stock-quantity">
                ${item.quantite} unités
            </div>
        </div>
    `).join('');
}

function ajouterStock() {
    const nom = prompt("Nom du produit:");
    if (!nom) return;
    const reference = prompt("Référence:");
    const quantite = parseInt(prompt("Quantité:"));
    const emplacement = prompt("Emplacement:");
    
    stockItems.push({ nom, reference, quantite, emplacement });
    localStorage.setItem('stockItems', JSON.stringify(stockItems));
    afficherStock();
}

// Gestion des livraisons
function afficherLivraisons() {
    const container = document.getElementById('livraison-list');
    if (!container) return;
    
    if (livraisons.length === 0) {
        container.innerHTML = '<p>Aucune livraison en cours.</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="delivery-timeline">
            ${['Commande passée', 'Préparation', 'Expédition', 'En transit', 'Livrée'].map((step, idx) => `
                <div class="timeline-step ${idx === 0 ? 'completed' : ''}">
                    <div class="timeline-icon">${idx === 0 ? '✓' : '○'}</div>
                    <div>${step}</div>
                </div>
            `).join('')}
        </div>
        <div class="livraison-list">
            ${livraisons.map(l => `
                <div class="stock-item">
                    <div><strong>${l.commande}</strong><br>Date prévue: ${l.date}</div>
                    <span class="status-badge status-warning">En cours</span>
                </div>
            `).join('')}
        </div>
    `;
}

function planifierLivraison() {
    const date = document.getElementById('date_livraison').value;
    const commande = document.getElementById('commande_livraison').value;
    
    if (!date || !commande) {
        alert("Veuillez sélectionner une date et une commande");
        return;
    }
    
    livraisons.push({ commande, date, statut: 'planifiée' });
    localStorage.setItem('livraisons', JSON.stringify(livraisons));
    afficherLivraisons();
    afficherCalendrier();
}

function afficherCalendrier() {
    const container = document.getElementById('calendrier-livraisons');
    if (!container) return;
    
    if (livraisons.length === 0) {
        container.innerHTML = '<p>Aucune livraison planifiée.</p>';
        return;
    }
    
    container.innerHTML = `
        <h4>Livraisons prévues:</h4>
        ${livraisons.map(l => `
            <div class="stock-item">
                <div><strong>${l.commande}</strong> - ${l.date}</div>
                <span class="status-badge status-success">Planifiée</span>
            </div>
        `).join('')}
    `;
}

// Gestion des utilisateurs
function afficherUtilisateurs() {
    const container = document.getElementById('user-list');
    if (!container) return;
    
    if (users.length === 0) {
        container.innerHTML = '<p>Aucun utilisateur enregistré.</p>';
        return;
    }
    
    container.innerHTML = users.map(user => `
        <div class="user-item">
            <div>
                <strong>${user.username}</strong><br>
                <small>${user.email}</small>
            </div>
            <div class="user-role">
                <span class="role-badge ${user.role === 'admin' ? 'admin' : user.role === 'stock' ? 'stock' : ''}">${user.role === 'admin' ? 'Admin' : user.role === 'stock' ? 'Stock' : 'Utilisateur'}</span>
                <button class="btn" onclick="supprimerUtilisateur('${user.username}')">🗑️</button>
            </div>
        </div>
    `).join('');
}

function ouvrirModalAjoutUser() {
    document.getElementById('modalUser').style.display = 'flex';
}

function fermerModalUser() {
    document.getElementById('modalUser').style.display = 'none';
    document.getElementById('new_username').value = '';
    document.getElementById('new_email').value = '';
    document.getElementById('new_password').value = '';
}

function ajouterUtilisateur() {
    const username = document.getElementById('new_username').value;
    const email = document.getElementById('new_email').value;
    const role = document.getElementById('new_role').value;
    const password = document.getElementById('new_password').value;
    
    if (!username || !email || !password) {
        alert("Veuillez remplir tous les champs");
        return;
    }
    
    users.push({ username, email, role, password });
    localStorage.setItem('users', JSON.stringify(users));
    fermerModalUser();
    afficherUtilisateurs();
}

function supprimerUtilisateur(username) {
    users = users.filter(u => u.username !== username);
    localStorage.setItem('users', JSON.stringify(users));
    afficherUtilisateurs();
}

// Charger les données au démarrage
document.addEventListener('DOMContentLoaded', () => {
    afficherStock();
    afficherLivraisons();
    afficherCalendrier();
    afficherUtilisateurs();
    
    // Charger les commandes pour le select
    fetch('/api/history', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    .then(res => res.json())
    .then(data => {
        const select = document.getElementById('commande_livraison');
        if (select) {
            select.innerHTML = '<option value="">Sélectionner une commande</option>' +
                (data.historique || []).map(h => `<option value="${h.reference}">${h.reference}</option>`).join('');
        }
    });
});
// ==================== AGENDA / CALENDRIER ====================
let currentDate = new Date();
let selectedDate = null;
let events = JSON.parse(localStorage.getItem('deliveryEvents') || '[]');

// Initialiser le calendrier
function initCalendar() {
    renderCalendar();
    afficherTousEvenements();
}

// Rendu du calendrier
function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDayOfMonth = new Date(year, month, 1);
    const startDayOfWeek = firstDayOfMonth.getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    // Ajuster pour commencer par lundi (0 = dimanche)
    const startOffset = startDayOfWeek === 0 ? 6 : startDayOfWeek - 1;
    
    const days = [];
    const prevMonthDays = new Date(year, month, 0).getDate();
    
    // Jours du mois précédent
    for (let i = startOffset - 1; i >= 0; i--) {
        days.push({ date: prevMonthDays - i, month: month - 1, isCurrentMonth: false });
    }
    
    // Jours du mois courant
    for (let i = 1; i <= daysInMonth; i++) {
        days.push({ date: i, month: month, isCurrentMonth: true });
    }
    
    // Jours du mois suivant
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
        days.push({ date: i, month: month + 1, isCurrentMonth: false });
    }
    
    // Afficher le mois et l'année
    const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
                        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
    document.getElementById('currentMonthYear').textContent = `${monthNames[month]} ${year}`;
    
    // Rendu des jours
    const calendarDays = document.getElementById('calendarDays');
    calendarDays.innerHTML = days.map(day => {
        const dateKey = `${year}-${String(day.month + 1).padStart(2, '0')}-${String(day.date).padStart(2, '0')}`;
        const hasEvent = events.some(e => e.date === dateKey);
        const isSelected = selectedDate === dateKey;
        
        return `
            <div class="calendar-day ${!day.isCurrentMonth ? 'other-month' : ''} ${hasEvent ? 'has-event' : ''} ${isSelected ? 'selected' : ''}"
                 onclick="selectDate('${dateKey}', ${day.date}, ${day.month}, ${year})">
                <span class="day-number">${day.date}</span>
            </div>
        `;
    }).join('');
}

// Changer de mois
function changeMonth(delta) {
    currentDate.setMonth(currentDate.getMonth() + delta);
    renderCalendar();
}

// Sélectionner une date
function selectDate(dateKey, day, month, year) {
    selectedDate = dateKey;
    const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
                        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
    document.getElementById('selectedDate').value = `${day} ${monthNames[month]} ${year}`;
    renderCalendar();
}

// Ajouter un événement
let currentFile = null;

document.getElementById('factureFile')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        currentFile = file;
        document.getElementById('fileNameDisplay').textContent = `📄 ${file.name}`;
        
        // Lire le fichier pour prévisualisation
        const reader = new FileReader();
        reader.onload = function(event) {
            currentFileData = event.target.result;
        };
        reader.readAsDataURL(file);
    }
});

let currentFileData = null;

function ajouterEvenement() {
    if (!selectedDate) {
        alert('Veuillez sélectionner une date dans le calendrier');
        return;
    }
    
    const hour = document.getElementById('eventHour').value;
    const minute = document.getElementById('eventMinute').value;
    const description = document.getElementById('eventDescription').value;
    
    if (!description) {
        alert('Veuillez ajouter une description de la livraison');
        return;
    }
    
    const event = {
        id: Date.now(),
        date: selectedDate,
        time: `${hour}:${minute}`,
        description: description,
        facture: currentFileData ? {
            name: currentFile.name,
            data: currentFileData,
            type: currentFile.type
        } : null,
        created_at: new Date().toISOString()
    };
    
    events.push(event);
    localStorage.setItem('deliveryEvents', JSON.stringify(events));
    
    // Réinitialiser le formulaire
    document.getElementById('eventDescription').value = '';
    document.getElementById('fileNameDisplay').textContent = '';
    document.getElementById('factureFile').value = '';
    currentFile = null;
    currentFileData = null;
    
    renderCalendar();
    afficherTousEvenements();
    
    alert('✅ Livraison ajoutée avec succès !');
}

// Afficher tous les événements
function afficherTousEvenements() {
    const container = document.getElementById('eventsList');
    if (!container) return;
    
    if (events.length === 0) {
        container.innerHTML = '<p>Aucune livraison planifiée.</p>';
        return;
    }
    
    // Trier par date
    const sortedEvents = [...events].sort((a, b) => a.date.localeCompare(b.date));
    
    container.innerHTML = sortedEvents.map(event => {
        const dateObj = new Date(event.date);
        const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
                            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
        const dateStr = `${dateObj.getDate()} ${monthNames[dateObj.getMonth()]} ${dateObj.getFullYear()}`;
        
        return `
            <div class="event-item">
                <div class="event-date">📅 ${dateStr}</div>
                <div class="event-time">⏰ ${event.time}</div>
                <div class="event-info">
                    <strong>Description:</strong><br>
                    ${event.description}
                </div>
                ${event.facture ? `
                    <div class="event-facture">
                        📄 Facture associée: <strong>${event.facture.name}</strong><br>
                        <button class="btn btn-primary" style="margin-top: 8px;" onclick="voirFacture(${event.id})">👁️ Voir la facture</button>
                    </div>
                ` : '<div class="event-facture">⚠️ Aucune facture associée</div>'}
                <div class="event-actions">
                    <button class="btn" style="background: #dc3545; color: white;" onclick="supprimerEvenement(${event.id})">🗑️ Supprimer</button>
                </div>
            </div>
        `;
    }).join('');
}

// Voir la facture
function voirFacture(eventId) {
    const event = events.find(e => e.id === eventId);
    if (!event || !event.facture) return;
    
    const modal = document.getElementById('modalFacture');
    const detailsDiv = document.getElementById('factureDetails');
    
    if (event.facture.type.includes('pdf')) {
        detailsDiv.innerHTML = `
            <p><strong>Fichier:</strong> ${event.facture.name}</p>
            <p><strong>Date de livraison:</strong> ${event.date} à ${event.time}</p>
            <p><strong>Description:</strong> ${event.description}</p>
            <embed src="${event.facture.data}" type="application/pdf" width="100%" height="400px">
        `;
    } else {
        detailsDiv.innerHTML = `
            <p><strong>Fichier:</strong> ${event.facture.name}</p>
            <p><strong>Date de livraison:</strong> ${event.date} à ${event.time}</p>
            <p><strong>Description:</strong> ${event.description}</p>
            <img src="${event.facture.data}" style="max-width: 100%; border-radius: 10px;">
        `;
    }
    
    modal.style.display = 'flex';
}

function fermerModalFacture() {
    document.getElementById('modalFacture').style.display = 'none';
}

// Supprimer un événement
function supprimerEvenement(eventId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette livraison ?')) {
        events = events.filter(e => e.id !== eventId);
        localStorage.setItem('deliveryEvents', JSON.stringify(events));
        renderCalendar();
        afficherTousEvenements();
    }
}

// Afficher les événements d'un jour spécifique
function afficherEvenementsJour(dateKey) {
    const eventsOfDay = events.filter(e => e.date === dateKey);
    if (eventsOfDay.length === 0) return null;
    
    return `
        <div style="margin-top: 10px;">
            ${eventsOfDay.map(e => `
                <div style="background: #e3f2fd; padding: 5px; border-radius: 5px; margin-top: 5px; font-size: 0.7rem;">
                    ${e.time} - ${e.description.substring(0, 20)}...
                </div>
            `).join('')}
        </div>
    `;
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    initCalendar();
    afficherTousEvenements();
});