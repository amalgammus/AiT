from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
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

    # Форма для выбора конфигурации (теперь используется только для генерации choices)
    select_form = APISelectForm()
    select_form.config.choices = [(c.id, c.name) for c in APIConfig.query.order_by(APIConfig.name)]

    # Форма для добавления/редактирования конфигурации
    config_form = APIConfigForm()

    api_methods = [
        {'name': 'ping', 'method': 'GET', 'description': 'Проверка доступности сервера'},
        {'name': 'get_crew_groups_list', 'method': 'GET', 'description': 'Получить список групп экипажа'},
        {'name': 'get_crew_info', 'method': 'GET', 'description': 'Получить информацию об экипаже'},
        {'name': 'get_order_states_list', 'method': 'GET', 'description': 'Получить список состояний заказа'},
        {'name': 'get_crew_states_list', 'method': 'GET', 'description': 'Получить список состояний экипажа'},
        {'name': 'change_order_state', 'method': 'POST', 'description': 'Изменить состояние заказа'},
    ]

    result = None
    selected_config = None

    # Обработка запроса на загрузку состояний
    if request.args.get('form_type') == 'load_states':
        try:
            config = APIConfig.query.first()
            if not config:
                return jsonify({'error': 'No API configurations available'}), 404

            client = APIClient(config.base_url, config.secret_key, config.verify_ssl)
            result = client.get_order_states_list()

            if result and result.get('code') == 0:
                return jsonify({
                    'states': result['data']['order_states']
                })
            return jsonify({
                'error': result.get('descr', 'Failed to load states') if result else 'Empty response from API'
            }), 400

        except Exception as e:
            return jsonify({
                'error': f'Error loading states: {str(e)}'
            }), 500

    # Обработка только явных действий
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        # Обработка сохранения конфигурации
        if form_type == 'save_config' and config_form.validate_on_submit():
            config_id = request.form.get('config_id')

            if config_form.is_default.data:
                APIConfig.query.update({'is_default': False})
                db.session.commit()

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
        elif form_type == 'execute_api':
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
                elif method_name == 'get_crew_states_list':
                    result = client.get_crew_states_list()
                elif method_name == 'change_order_state':
                    order_id = request.form.get('order_id', '').strip()
                    new_state = request.form.get('new_state', '').strip()
                    penalty_sum = request.form.get('cancel_order_penalty_sum', '').strip()

                    if not order_id or not new_state:
                        raise ValueError("order_id и new_state обязательны")

                    result = client.change_order_state(
                        order_id=int(order_id),
                        new_state=int(new_state),
                        cancel_order_penalty_sum=float(penalty_sum) if penalty_sum else None
                    )
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
                           result_json=result if result else None,
                           selected_config=selected_config,
                           method_name=request.form.get('api_method') if request.method == 'POST' else None)


@api_bp.route('/get_config', methods=['GET'])
@login_required
def get_config():
    if not current_user.is_admin:
        abort(403)

    config_id = request.args.get('config_id')
    if config_id:
        config = APIConfig.query.get(config_id)
        if config:
            return jsonify({
                'config': {
                    'id': config.id,
                    'name': config.name,
                    'base_url': config.base_url,
                    'secret_key': config.secret_key,
                    'verify_ssl': config.verify_ssl,
                    'is_default': config.is_default
                }
            })
    return jsonify({'config': None})
