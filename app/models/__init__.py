from .user import User
from .department import Department
from .api_config import APIConfig
from .mysql_config import MySQLConfig

# Явный экспорт моделей
__all__ = ['User', 'Department', 'APIConfig', 'MySQLConfig']
