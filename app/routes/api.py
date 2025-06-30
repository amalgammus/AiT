from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user

from app import db
from app.models.api_config import APIConfig
from app.routes.forms import APIConfigForm, APISelectForm
from app.api import APIClient
import json

api_bp = Blueprint('api', __name__)


@api_bp.route('/api_console', methods=['GET', 'POST'])
@login_required
def api_console():
    if not current_user.is_admin:
        abort(403)

    # Форма для выбора конфигурации
    select_form = APISelectForm()
    select_form.config.choices = [(c.id, c.name) for c in APIConfig.query.order_by(APIConfig.name)]

    # Форма для добавления/редактирования конфигурации
    config_form = APIConfigForm()

    api_methods = [
        {'name': 'ping', 'method': 'GET', 'description': 'Проверка доступности сервера'},
        {'name': 'get_crew_groups_list', 'method': 'GET', 'description': 'Получить список групп экипажа'},
        {'name': 'get_crew_info', 'method': 'GET', 'description': 'Получить информацию об экипаже'},
        {'name': 'get_order_states_list', 'method': 'GET', 'description': 'Получить список состояний заказа'},
    ]

    result = None
    selected_config = None

    # Обработка выбора конфигурации
    if select_form.validate_on_submit() and request.form.get('form_type') == 'select_config':
        selected_config = APIConfig.query.get(select_form.config.data)
        if selected_config:
            config_form = APIConfigForm(obj=selected_config)

    # Обработка сохранения конфигурации
    elif config_form.validate_on_submit() and request.form.get('form_type') == 'save_config':
        config_id = request.form.get('config_id')

        # Сброс других default, если выбран этот
        if config_form.is_default.data:
            APIConfig.query.update({'is_default': False})
            db.session.commit()  # Важно: коммитим перед созданием/обновлением новой записи

        if config_id:
            config = APIConfig.query.get(config_id)
            if config:
                config_form.populate_obj(config)
        else:
            config = APIConfig()
            config_form.populate_obj(config)
            db.session.add(config)

        db.session.commit()
        flash('Configuration saved successfully', 'success')
        return redirect(url_for('api.api_console'))

    # Обработка выполнения API запроса
    if request.method == 'POST':
        try:
            config_id = request.form.get('selected_config_id')
            if config_id:
                config = APIConfig.query.get(config_id)
                if not config:
                    raise ValueError("Selected configuration not found")
            else:
                config = APIConfig.query.filter_by(is_default=True).first()
                if not config:
                    raise ValueError("No default configuration found")

            client = APIClient(config.base_url, config.secret_key, config.verify_ssl)
            method_name = request.form.get('api_method')

            if method_name == 'ping':
                result = client.ping()
            elif method_name == 'get_crew_groups_list':
                result = client.get_crew_groups_list()
            elif method_name == 'get_crew_info':
                crew_id = request.form.get('crew_id', '').strip()
                fields = request.form.get('fields', '').strip()
                if not crew_id:
                    raise ValueError("crew_id is required")
                result = client.get_crew_info(crew_id=int(crew_id), fields=fields if fields else None)
            elif method_name == 'get_order_states_list':
                result = client.get_order_states_list()
            else:
                result = {
                    "code": -1,
                    "descr": "Метод не реализован",
                    "data": {}
                }

        except Exception as e:
            result = {
                "code": -1,
                "descr": f"Ошибка: {str(e)}",
                "data": {}
            }

    return render_template('api/console.html',
                           select_form=select_form,
                           config_form=config_form,
                           api_methods=api_methods,
                           result=json.dumps(result, indent=2, ensure_ascii=False) if result else None,
                           result_json=result if result else None,  # Добавляем распарсенный JSON
                           selected_config=selected_config,
                           method_name=request.form.get('api_method') if request.method == 'POST' else None)

