from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models.department import Department
from app.extensions import db
from .forms import DepartmentForm

department_bp = Blueprint('department', __name__)


@department_bp.route('/departments')
@login_required
def list_departments():
    if not current_user.is_admin:
        abort(403)

    departments = Department.query.all()
    return render_template('department/list.html', departments=departments)


@department_bp.route('/departments/create', methods=['GET', 'POST'])
@login_required
def create_department():
    if not current_user.is_admin:
        abort(403)

    form = DepartmentForm()

    if form.validate_on_submit():
        department = Department(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(department)
        db.session.commit()
        flash('Department created successfully', 'success')
        return redirect(url_for('department.list_departments'))

    return render_template('department/create.html', form=form)


@department_bp.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    if not current_user.is_admin:
        abort(403)

    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)

    if form.validate_on_submit():
        department.name = form.name.data
        department.description = form.description.data
        db.session.commit()
        flash('Department updated successfully', 'success')
        return redirect(url_for('department.list_departments'))

    return render_template('department/edit.html', form=form, department=department)


@department_bp.route('/departments/<int:id>/delete', methods=['POST'])
@login_required
def delete_department(id):
    if not current_user.is_admin:
        abort(403)

    department = Department.query.get_or_404(id)

    if department.users:
        flash('Cannot delete department with users', 'danger')
    else:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted successfully', 'success')

    return redirect(url_for('department.list_departments'))
