from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import login_manager
from typing import Optional


@login_manager.user_loader
def load_user(user_id: int) -> Optional['User']:
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    department = db.relationship('Department', backref='users')

    def __init__(self,
                 username: str,
                 email: str,
                 is_admin: bool = False,
                 department_id: Optional[int] = None):
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self.department_id = department_id

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
