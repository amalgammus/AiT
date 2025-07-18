import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/user_management')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_LOG_LEVEL = 'WARNING'
