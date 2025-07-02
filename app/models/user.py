from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    department = db.relationship('Department', backref='users')

    def __init__(self, username, email, is_admin=False, department_id=None):
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self.department_id = department_id

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Установка хешированного пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Требуется для Flask-Login (переопределение стандартного метода)"""
        return str(self.id)
