from flask import Blueprint

# Инициализация Blueprints
auth_bp = Blueprint('auth', __name__)
user_bp = Blueprint('user', __name__)
department_bp = Blueprint('department', __name__)
api_bp = Blueprint('api', __name__)
mysql_bp = Blueprint('mysql_query', __name__)


# Явная регистрация маршрутов (после создания Blueprint)
def register_routes():
    """Регистрация всех обработчиков маршрутов"""
    from .auth import login, logout
    from .user import list_users, create_user, edit_user, user_profile, delete_user
    from .department import (
        list_departments,
        create_department,
        edit_department,
        delete_department
    )
    from .api import api_console, get_config
    from .mysql_query import mysql_query

    # Auth routes
    auth_bp.add_url_rule('/', 'home', login)
    auth_bp.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    auth_bp.add_url_rule('/logout', 'logout', logout)

    # User routes
    user_bp.add_url_rule('/users', 'list_users', list_users)
    user_bp.add_url_rule('/users/create', 'create_user', create_user, methods=['GET', 'POST'])
    user_bp.add_url_rule('/users/<int:user_id>/edit', 'edit_user', edit_user, methods=['GET', 'POST'])
    user_bp.add_url_rule('/profile', 'user_profile', user_profile, methods=['GET', 'POST'])
    user_bp.add_url_rule('/users/<int:user_id>/delete', 'delete_user', delete_user, methods=['POST'])

    # Department routes
    department_bp.add_url_rule('/departments', 'list_departments', list_departments)
    department_bp.add_url_rule('/departments/create', 'create_department',
                               create_department, methods=['GET', 'POST'])
    department_bp.add_url_rule('/departments/<int:dept_id>/edit', 'edit_department',
                               edit_department, methods=['GET', 'POST'])
    department_bp.add_url_rule('/departments/<int:dept_id>/delete', 'delete_department',
                               delete_department, methods=['POST'])

    # API routes
    api_bp.add_url_rule('/api_console', 'api_console', api_console, methods=['GET', 'POST'])
    api_bp.add_url_rule('/get_config', 'get_config', get_config, methods=['GET'])

    # MySQL routes
    mysql_bp.add_url_rule('/mysql_query', 'mysql_query', mysql_query, methods=['GET', 'POST'])


register_routes()  # Выполняем регистрацию
