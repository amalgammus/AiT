from app.extensions import db


class APIConfig(db.Model):
    __tablename__ = 'api_configs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_url = db.Column(db.String(255), nullable=False)
    secret_key = db.Column(db.String(255), nullable=False)
    verify_ssl = db.Column(db.Boolean, default=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<APIConfig {self.name}>'
