from flask import Flask
from .extensions import db, login_manager, migrate


def create_app(config_class='app.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Настройка Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Импорт моделей после инициализации db
    with app.app_context():
        from .models.user import User

        @login_manager.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

    # Регистрация Blueprints
    from .routes import auth_bp, user_bp, department_bp, api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
