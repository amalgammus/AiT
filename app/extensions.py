from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


db = SQLAlchemy()
login_manager = LoginManager()
# login_manager.login_view = 'auth.login'
migrate = Migrate()
