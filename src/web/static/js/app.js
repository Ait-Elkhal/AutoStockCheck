// ==================== APP DATA - GLOBAL STATE ====================

const AppData = {
    // État global
    currentUser: null,
    isAuthenticated: false,
    userRole: null,
    
    // Données métier
    stock: [],
    factures: [],
    commandes: [],
    clients: [],
    anomalies: [],
    
    // Notifications
    notifications: [],
    unreadCount: 0,
    
    // Écouteurs d'événements
    listeners: {
        stock: [],
        factures: [],
        commandes: [],
        clients: [],
        anomalies: [],
        user: [],
        notifications: []
    },
    
    // ==================== INITIALISATION ====================
    async init() {
        console.log('🔄 Initialisation AppData...');
        await this.loadCurrentUser();
        await this.loadAllData();
        console.log('✅ AppData initialisé');
    },
    
    // ==================== UTILISATEUR ====================
    async loadCurrentUser() {
        try {
            const response = await fetch('/api/me');
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    this.currentUser = data.user;
                    this.isAuthenticated = true;
                    this.userRole = data.user.role;
                    this.notify('user', this.currentUser);
                }
            } else {
                this.isAuthenticated = false;
                this.currentUser = null;
            }
        } catch(e) {
            console.error('Erreur chargement utilisateur:', e);
            this.isAuthenticated = false;
        }
    },
    
    // ==================== CHARGEMENT DES DONNÉES ====================
    async loadAllData() {
        if (!this.isAuthenticated) return;
        
        await Promise.all([
            this.loadStock(),
            this.loadFactures(),
            this.loadCommandes(),
            this.loadClients(),
            this.loadAnomalies(),
            this.loadNotifications()
        ]);
    },
    
    async loadStock() {
        try {
            const response = await fetch('/api/stock');
            const data = await response.json();
            if (data.status === 'success') {
                this.stock = data.stock;
                this.notify('stock', this.stock);
                console.log(`📦 Stock chargé: ${this.stock.length} produits`);
            }
        } catch(e) { console.error('Erreur stock:', e); }
    },
    
    async loadFactures() {
        try {
            const response = await fetch('/api/factures-recues');
            const data = await response.json();
            if (data.status === 'success') {
                this.factures = data.factures;
                this.notify('factures', this.factures);
                console.log(`📄 Factures chargées: ${this.factures.length}`);
            }
        } catch(e) { console.error('Erreur factures:', e); }
    },
    
    async loadCommandes() {
        try {
            const response = await fetch('/api/commandes-recues');
            const data = await response.json();
            if (data.status === 'success') {
                this.commandes = data.commandes;
                this.notify('commandes', this.commandes);
                console.log(`📦 Commandes chargées: ${this.commandes.length}`);
            }
        } catch(e) { console.error('Erreur commandes:', e); }
    },
    
    async loadClients() {
        try {
            const response = await fetch('/api/clients');
            const data = await response.json();
            if (data.status === 'success') {
                this.clients = data.clients;
                this.notify('clients', this.clients);
                console.log(`👥 Clients chargés: ${this.clients.length}`);
            }
        } catch(e) { console.error('Erreur clients:', e); }
    },
    
    async loadAnomalies() {
        try {
            const response = await fetch('/api/matching/anomalies');
            const data = await response.json();
            if (data.status === 'success') {
                this.anomalies = data.anomalies;
                this.notify('anomalies', this.anomalies);
                console.log(`🔧 Anomalies chargées: ${this.anomalies.length}`);
            }
        } catch(e) { console.error('Erreur anomalies:', e); }
    },
    
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            if (data.status === 'success') {
                this.notifications = data.notifications || [];
                this.unreadCount = this.notifications.filter(n => !n.read).length;
                this.notify('notifications', this.notifications);
            }
        } catch(e) { console.error('Erreur notifications:', e); }
    },
    
    // ==================== MISE À JOUR ====================
    async refreshAll() {
        console.log('🔄 Rafraîchissement global des données...');
        await this.loadAllData();
        window.dispatchEvent(new CustomEvent('appdata-refreshed'));
    },
    
    async refreshStock() { await this.loadStock(); },
    async refreshFactures() { await this.loadFactures(); },
    async refreshCommandes() { await this.loadCommandes(); },
    async refreshClients() { await this.loadClients(); },
    async refreshAnomalies() { await this.loadAnomalies(); },
    async refreshNotifications() { await this.loadNotifications(); },
    
    // ==================== CRUD STOCK ====================
    async addProduct(productData) {
        const response = await fetch('/api/stock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });
        if (response.ok) {
            await this.refreshStock();
            this.showToast('Produit ajouté', 'success');
            return true;
        }
        return false;
    },
    
    async updateProduct(id, productData) {
        const response = await fetch(`/api/stock/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });
        if (response.ok) {
            await this.refreshStock();
            this.showToast('Produit modifié', 'success');
            return true;
        }
        return false;
    },
    
    async deleteProduct(id) {
        const response = await fetch(`/api/stock/${id}`, { method: 'DELETE' });
        if (response.ok) {
            await this.refreshStock();
            this.showToast('Produit supprimé', 'success');
            return true;
        }
        return false;
    },
    
    // ==================== NOTIFICATIONS ====================
    markNotificationAsRead(id) {
        fetch(`/api/notifications/${id}/read`, { method: 'POST' })
            .then(() => this.refreshNotifications());
    },
    
    markAllNotificationsAsRead() {
        this.notifications.forEach(n => {
            if (!n.read) this.markNotificationAsRead(n.id);
        });
    },
    
    // ==================== SUBSCRIBE / NOTIFY ====================
    subscribe(type, callback) {
        if (!this.listeners[type]) return;
        this.listeners[type].push(callback);
        // Appel immédiat avec les données existantes
        if (this[type] && this[type].length) callback(this[type]);
    },
    
    notify(type, data) {
        if (this.listeners[type]) {
            this.listeners[type].forEach(cb => cb(data));
        }
    },
    
    // ==================== UTILITAIRES ====================
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<span>${message}</span><button class="toast-close" onclick="this.parentElement.remove()">✕</button>`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    },
    
    // Getters
    getStockByReference(ref) {
        return this.stock.find(p => p.reference === ref);
    },
    
    getProductById(id) {
        return this.stock.find(p => p.id == id);
    },
    
    getClientById(id) {
        return this.clients.find(c => c.id == id);
    },
    
    getFactureById(id) {
        return this.factures.find(f => f.id == id);
    },
    
    getCommandeById(id) {
        return this.commandes.find(c => c.id == id);
    }
};

// Exporter globalement
window.AppData = AppData;

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    AppData.init();
});