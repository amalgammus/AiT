import sys
from datetime import datetime, timedelta

import pymysql
from flask import Blueprint, render_template, request, flash, abort, redirect, url_for
from flask_login import login_required, current_user
from pymysql.cursors import DictCursor

from app import db
from app.models import MySQLConfig
from app.routes.forms import MySQLQueryForm

mysql_bp = Blueprint('mysql_query', __name__)


def debug_log(message):
    print(f"[DEBUG] {message}", file=sys.stderr)
    sys.stderr.flush()


def get_db_config():
    return MySQLConfig.query.first()


def get_db_connection():
    config = get_db_config()
    if not config:
        raise ValueError("MySQL configuration not found")

    return pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.username,
        password=config.password,
        database=config.database,
        cursorclass=pymysql.cursors.DictCursor
    )


@mysql_bp.route('/mysql_query', methods=['GET', 'POST'])
@login_required
def mysql_query():
    if not current_user.is_admin:
        abort(403)

    config = get_db_config()
    form = MySQLQueryForm()
    results = None

    # Устанавливаем только даты по умолчанию при GET-запросе
    if request.method == 'GET':
        first_day = datetime.now() - timedelta(days=30)
        last_day = datetime.now()

        form.start_date.data = first_day
        form.end_date.data = last_day
    elif form.validate_on_submit():  # Выполняем запрос только при отправке формы

        query = """
            SELECT 
                p.name as 'Project', u.lastname as 'Employee', iss.subject as 'Subject', 
                SUM(te.hours) as 'Hours'
            FROM time_entries te 
            LEFT JOIN issues iss ON te.issue_id = iss.id
            LEFT JOIN issues ir ON iss.root_id = ir.id
            JOIN custom_values cv ON cv.customized_id = ir.id
            JOIN custom_fields cf ON cv.custom_field_id = cf.id
            JOIN projects p ON te.project_id = p.id
            JOIN users u ON te.user_id = u.id
            WHERE te.spent_on BETWEEN %s AND %s
            AND cf.id = 6
            AND cv.value = %s
            GROUP BY p.name, u.lastname, iss.subject
        """

        params = (
            form.start_date.data.strftime('%Y-%m-%d %H:%M:%S'),
            form.end_date.data.strftime('%Y-%m-%d %H:%M:%S'),
            str(form.client_id.data)
        )

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
        except Exception as e:
            debug_log(f"Ошибка запроса: {str(e)}")
            flash(f'Ошибка выполнения запроса: {str(e)}', 'danger')

    return render_template(
        'mysql/query.html',
        form=form,
        results=results,
        config=config  # Теперь передаем конфиг в шаблон
    )


@mysql_bp.route('/update_mysql_config', methods=['POST'])
@login_required
def update_mysql_config():
    if not current_user.is_admin:
        abort(403)

    try:
        config_id = request.form.get('config_id')
        name = request.form['name']
        host = request.form['host']
        port = int(request.form['port'])
        database = request.form['database']
        username = request.form['username']
        password = request.form['password']

        if config_id:
            config = MySQLConfig.query.get(config_id)
            if config:
                config.name = name
                config.host = host
                config.port = port
                config.database = database
                config.username = username
                config.password = password

        db.session.commit()
        flash('Настройки подключения обновлены', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка: {str(e)}', 'danger')

    return redirect(url_for('mysql_query.mysql_query'))
