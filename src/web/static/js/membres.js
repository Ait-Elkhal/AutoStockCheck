// ==================== MEMBRES.JS ====================

let membres = [];
let currentIndex = 0;
let currentView = 'carousel';
let currentTeam = 'all';
let currentMembreId = null;
let thumbScrollPosition = 0;

// Données initiales
const membresData = [
    { id: 1, nom: "Ahmed Benali", email: "ahmed.benali@autostock.com", tel: "+212 6 12 34 56 78", nationalite: "Maroc", sexe: "Homme", role: "Admin", equipe: "direction", dateEntree: "2024-01-15", avatar: "👑", cv: "cv_ahmed.pdf" },
    { id: 2, nom: "Fatima Zahra", email: "fatima.zahra@autostock.com", tel: "+212 6 23 45 67 89", nationalite: "Maroc", sexe: "Femme", role: "Responsable Stock", equipe: "stock", dateEntree: "2024-02-01", avatar: "🏭", cv: "cv_fatima.pdf" },
    { id: 3, nom: "Karim Idrissi", email: "karim.idrissi@autostock.com", tel: "+212 6 34 56 78 90", nationalite: "Maroc", sexe: "Homme", role: "Réceptionnaire", equipe: "reception", dateEntree: "2024-02-15", avatar: "📥", cv: "cv_karim.pdf" },
    { id: 4, nom: "Sofia Mansouri", email: "sofia.mansouri@autostock.com", tel: "+212 6 45 67 89 01", nationalite: "France", sexe: "Femme", role: "Qualité", equipe: "qualite", dateEntree: "2024-03-01", avatar: "🔧", cv: "cv_sofia.pdf" },
    { id: 5, nom: "Yassine Chakir", email: "yassine.chakir@autostock.com", tel: "+212 6 56 78 90 12", nationalite: "Maroc", sexe: "Homme", role: "Camionneur", equipe: "livraison", dateEntree: "2024-03-10", avatar: "🚚", cv: "cv_yassine.pdf" },
    { id: 6, nom: "Nadia Tazi", email: "nadia.tazi@autostock.com", tel: "+212 6 67 89 01 23", nationalite: "Maroc", sexe: "Femme", role: "Informatique", equipe: "informatique", dateEntree: "2024-03-15", avatar: "💻", cv: "cv_nadia.pdf" }
];

function loadMembres() {
    const stored = localStorage.getItem('membres');
    membres = stored ? JSON.parse(stored) : membresData;
    updateDisplay();
}

function getFilteredMembres() {
    if (currentTeam === 'all') return membres;
    return membres.filter(m => m.equipe === currentTeam);
}

function updateDisplay() {
    const filtered = getFilteredMembres();
    if (filtered.length === 0) return;
    
    if (currentView === 'carousel') {
        document.getElementById('carouselView').style.display = 'flex';
        document.getElementById('listView').style.display = 'none';
        updateMainCard(filtered[currentIndex] || filtered[0]);
        updateThumbnails(filtered);
    } else {
        document.getElementById('carouselView').style.display = 'none';
        document.getElementById('listView').style.display = 'block';
        updateListView(filtered);
    }
}

function updateMainCard(m) {
    if (!m) return;
    currentMembreId = m.id;
    document.getElementById('membreAvatar').textContent = m.avatar || getAvatarIcon(m.role);
    document.getElementById('membreNom').textContent = m.nom;
    document.getElementById('membreRole').textContent = m.role;
    document.getElementById('membreEquipe').innerHTML = `<span class="equipe-badge equipe-${m.equipe}">${getEquipeLabel(m.equipe)}</span>`;
    document.getElementById('membreEmail').textContent = m.email;
    document.getElementById('membreTel').textContent = m.tel;
    document.getElementById('membreNationalite').textContent = m.nationalite;
    document.getElementById('membreSexe').textContent = m.sexe;
    document.getElementById('membreDateEntree').textContent = formatDate(m.dateEntree);
}

function updateThumbnails(filtered) {
    const container = document.getElementById('thumbnails');
    container.innerHTML = filtered.map((m, idx) => `
        <div class="thumbnail-card ${idx === currentIndex ? 'active' : ''}" onclick="goToMembre(${idx})">
            <div class="thumb-avatar">${m.avatar || getAvatarIcon(m.role)}</div>
            <div class="thumb-name">${m.nom.split(' ')[0]}</div>
            <div class="thumb-role">${m.role}</div>
        </div>
    `).join('');
}

function updateListView(filtered) {
    const tbody = document.getElementById('membresTableBody');
    tbody.innerHTML = filtered.map(m => `
        <tr>
            <td><div class="table-avatar">${m.avatar || getAvatarIcon(m.role)}</div></td>
            <td><strong>${m.nom}</strong></td>
            <td>${m.email}</td>
            <td>${m.tel}</td>
            <td>${m.role}</td>
            <td><span class="equipe-badge equipe-${m.equipe}">${getEquipeLabel(m.equipe)}</span></td>
            <td>${m.nationalite}</td>
            <td>${m.sexe}</td>
            <td>${formatDate(m.dateEntree)}</td>
            <td><button class="btn-icon" onclick="downloadCV(${m.id})">📄</button></td>
            <td><button class="btn-icon edit" onclick="editMembre(${m.id})">✏️</button><button class="btn-icon delete" onclick="deleteMembre(${m.id})">🗑️</button></td>
        </tr>
    `).join('');
}

function prevMembre() { const f = getFilteredMembres(); currentIndex = (currentIndex - 1 + f.length) % f.length; updateDisplay(); }
function nextMembre() { const f = getFilteredMembres(); currentIndex = (currentIndex + 1) % f.length; updateDisplay(); }
function goToMembre(idx) { currentIndex = idx; updateDisplay(); }

function scrollThumbs(d) {
    const wrapper = document.getElementById('thumbnailsWrapper');
    thumbScrollPosition += d * 200;
    wrapper.scrollTo({ left: thumbScrollPosition, behavior: 'smooth' });
}

function setView(view) {
    currentView = view;
    document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    updateDisplay();
}

function filterByTeam(team) {
    currentTeam = team;
    document.querySelectorAll('.team-filter').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    currentIndex = 0;
    updateDisplay();
}

// Modal functions
function openMembreModal() { document.getElementById('modalTitle').innerHTML = '➕ Nouveau membre'; document.getElementById('editMembreId').value = ''; document.getElementById('membreModal').style.display = 'flex'; }
function closeMembreModal() { document.getElementById('membreModal').style.display = 'none'; }

function editMembre(id) {
    const m = membres.find(m => m.id === id);
    if (!m) return;
    document.getElementById('modalTitle').innerHTML = '✏️ Modifier membre';
    document.getElementById('editMembreId').value = m.id;
    document.getElementById('membreNomComplet').value = m.nom;
    document.getElementById('membreSexeSelect').value = m.sexe;
    document.getElementById('membreEmailSelect').value = m.email;
    document.getElementById('membreTelSelect').value = m.tel;
    document.getElementById('membreNationaliteSelect').value = m.nationalite;
    document.getElementById('membreDateEntreeSelect').value = m.dateEntree;
    document.getElementById('membreRoleSelect').value = m.role;
    document.getElementById('membreEquipeSelect').value = m.equipe;
    document.getElementById('membreModal').style.display = 'flex';
}

function saveMembre() {
    alert('✅ Membre sauvegardé (démonstration)');
    closeMembreModal();
}

function deleteMembre(id) {
    if (confirm('Supprimer ce membre définitivement ?')) {
        membres = membres.filter(m => m.id !== id);
        localStorage.setItem('membres', JSON.stringify(membres));
        if (currentIndex >= membres.length) currentIndex = 0;
        updateDisplay();
    }
}

function downloadCV(id) { alert(`📄 Téléchargement du CV (ID: ${id})`); }

// Utilitaires
function getAvatarIcon(role) {
    const icons = { 'Admin': '👑', 'Responsable Stock': '🏭', 'Réceptionnaire': '📥', 'Qualité': '🔧', 'Camionneur': '🚚', 'Auditeur': '📊', 'Informatique': '💻' };
    return icons[role] || '👤';
}

function getEquipeLabel(equipe) {
    const labels = { 'direction': '👑 Direction', 'stock': '🏭 Stock', 'reception': '📥 Réception', 'qualite': '🔧 Qualité', 'livraison': '🚚 Livraison', 'informatique': '💻 Informatique' };
    return labels[equipe] || equipe;
}

function formatDate(date) { if (!date) return '-'; const d = new Date(date); return d.toLocaleDateString(); }

// Initialisation
loadMembres();

// Export global
window.prevMembre = prevMembre; window.nextMembre = nextMembre; window.goToMembre = goToMembre;
window.setView = setView; window.filterByTeam = filterByTeam; window.scrollThumbs = scrollThumbs;
window.openMembreModal = openMembreModal; window.closeMembreModal = closeMembreModal;
window.editMembre = editMembre; window.saveMembre = saveMembre; window.deleteMembre = deleteMembre;
window.downloadCV = downloadCV;