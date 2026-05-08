from flask import render_template, request
from auth import require_auth

def register_dashboard_routes(app):
    @app.route('/api/dashboard/section/<section>', methods=['GET'])
    @require_auth
    def dashboard_section(section):
        allowed_sections = {
            'admin': ['dashboard', 'reception', 'reception_reelle', 'matching', 'historique', 'guide', 'stock', 'livraison', 'date-livraison', 'gestion-utilisateurs', 'admin-dashboard', 'gestion-clients-unifie', 'qualite-anomalies'],
            'stock': ['dashboard', 'reception', 'reception_reelle', 'matching', 'historique', 'guide', 'stock', 'livraison', 'date-livraison', 'qualite-anomalies'],
            'user': ['dashboard', 'historique', 'guide', 'livraison', 'date-livraison']
        }
        
        if section not in allowed_sections.get(request.user_role, []):
            return "<div class='dashboard-card'><p>⛔ Accès non autorisé</p></div>", 403
        
        templates = {
            'dashboard': 'dashboard/sections/dashboard.html',
            'reception': 'dashboard/sections/reception.html',
            'reception_reelle': 'dashboard/sections/reception_reelle.html',
            'matching': 'dashboard/sections/matching.html',
            'historique': 'dashboard/sections/historique.html',
            'guide': 'dashboard/sections/guide.html',
            'stock': 'dashboard/sections/stock.html',
            'livraison': 'dashboard/sections/livraison.html',
            'date-livraison': 'dashboard/sections/date-livraison.html',
            'gestion-utilisateurs': 'dashboard/sections/gestion-utilisateurs.html',
            'admin-dashboard': 'dashboard/sections/admin-dashboard.html',
            'gestion-clients-unifie': 'dashboard/sections/gestion-clients-unifie.html',
            'qualite-anomalies': 'dashboard/sections/qualite-anomalies.html'
        }
        
        template = templates.get(section, 'dashboard/sections/dashboard.html')
        try:
            return render_template(template, role=request.user_role)
        except Exception as e:
            return f"<div class='dashboard-card'><p>❌ Erreur: {str(e)}</p></div>", 500