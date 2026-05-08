from flask import render_template, request
from auth import require_auth

def register_administration_routes(app):
    @app.route('/api/administration/section/<section>', methods=['GET'])
    @require_auth
    def administration_section(section):
        if request.user_role not in ['admin', 'manager', 'auditeur']:
            return "⛔ Accès non autorisé", 403
        
        templates = {
            'clients': 'administration/sections/clients.html',
            'membres': 'administration/sections/membres.html',
            'receptions': 'administration/sections/receptions.html',
            'stock': 'administration/sections/stock.html',
            'emails': 'administration/sections/emails.html',
            'statistiques': 'administration/sections/statistiques.html',
             
        }
        
        template = templates.get(section, 'administration/sections/clients.html')
        return render_template(template, role=request.user_role)