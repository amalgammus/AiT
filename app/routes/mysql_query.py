from flask import Blueprint, render_template, request, flash, abort
from flask_login import login_required, current_user
from app.models import MySQLConfig
from app.routes.forms import MySQLQueryForm
import pymysql
from datetime import datetime, timedelta
import sys

mysql_bp = Blueprint('mysql_query', __name__)


def debug_log(message):
    print(f"[DEBUG] {message}", file=sys.stderr)
    sys.stderr.flush()


def get_default_config():
    config = MySQLConfig.query.filter_by(is_default=True).first()
    if config:
        debug_log(f"Конфигурация найдена: {config.name} ({config.host})")
    return config


def get_db_connection(config):
    try:
        return pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            database=config.database,
            cursorclass=pymysql.cursors.DictCursor
        )
    except pymysql.Error as e:
        debug_log(f"Ошибка подключения: {e}")
        raise


@mysql_bp.route('/mysql_query', methods=['GET', 'POST'])
@login_required
def mysql_query():
    if not current_user.is_admin:
        abort(403)

    config = get_default_config()
    if not config:
        flash('Не найдена конфигурация MySQL по умолчанию', 'danger')
        return render_template('mysql/query.html', form=MySQLQueryForm())

    form = MySQLQueryForm()
    results = None

    # Устанавливаем только даты по умолчанию при GET-запросе
    if request.method == 'GET':
        first_day = datetime.now() - timedelta(days=30)
        last_day = datetime.now()

        form.start_date.data = first_day
        form.end_date.data = last_day
    elif form.validate_on_submit():  # Выполняем запрос только при отправке формы
        debug_log("Форма отправлена, выполняем запрос...")

        query = """
            SELECT 
                p.name as 'Project', u.lastname as 'Employee', iss.subject as 'Task',  
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
            with get_db_connection(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    debug_log(f"Получено {len(results)} записей")
        except Exception as e:
            debug_log(f"Ошибка запроса: {str(e)}")
            flash(f'Ошибка выполнения запроса: {str(e)}', 'danger')

    return render_template(
        'mysql/query.html',
        form=form,
        results=results,
        config=config
    )
