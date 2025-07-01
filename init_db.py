from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    # Create tables
    db.create_all()

    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created with username 'admin' and password 'admin123'")

    print("Database initialized successfully")
