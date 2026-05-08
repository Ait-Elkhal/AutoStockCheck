from flask import render_template, send_from_directory

def register_pages_routes(app):
    @app.route('/')
    def accueil():
        return render_template('pages/accueil.html', active_page='accueil')
    
    @app.route('/models')
    def models():
        return render_template('pages/models.html', active_page='models')
    
    @app.route('/contact')
    def contact():
        return render_template('pages/contact.html', active_page='contact')
    
    @app.route('/login')
    def login_page():
        return render_template('pages/login.html', active_page='login')
    
    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard/index.html')
    
    @app.route('/administration')
    def administration_page():
        return render_template('administration/index.html')
    
    @app.route('/static/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)
    