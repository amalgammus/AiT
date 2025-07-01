from flask import Flask, render_template, redirect, url_for, flash, request
from app.config import Config
from app.extensions import db, login_manager, migrate
from sqlalchemy.exc import IntegrityError
import logging


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.department import department_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Login manager settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    logging.getLogger('app.api').setLevel(Config.API_LOG_LEVEL)

    @app.errorhandler(403)
    def forbidden_error(_):
        return render_template('403.html'), 403

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(_):
        db.session.rollback()
        flash('Ошибка сохранения: такие данные уже существуют', 'danger')
        return redirect(request.referrer or url_for('user.list_users'))

    return app
