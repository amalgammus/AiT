from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.department import Department
from app.models.user import User
from .forms import UserForm, UserEditForm, UserProfileForm, AdminProfileForm

user_bp = Blueprint('user', __name__)


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    form_class = AdminProfileForm if current_user.is_admin else UserProfileForm
    form = form_class(obj=current_user)

    # Для админов загружаем отделы
    if current_user.is_admin and hasattr(form, 'department_id'):
        form.department_id.choices = [(d.id, d.name) for d in Department.query.all()]

    if form.validate_on_submit():
        try:
            current_user.username = form.username.data
            current_user.email = form.email.data

            if form.password.data:
                current_user.set_password(form.password.data)

            if current_user.is_admin:
                current_user.is_admin = form.is_admin.data
                current_user.department_id = form.department_id.data

            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('user.user_profile'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: username or email already exists', 'danger')

    return render_template('user/profile.html',
                           form=form,
                           current_user=current_user,
                           is_admin=current_user.is_admin)


@user_bp.route('/users')
@login_required
def list_users():
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    return render_template('user/list.html',
                           users=users,
                           can_edit=current_user.is_admin)


@user_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        abort(403)

    form = UserForm()
    form.department_id.choices = [(d.id, d.name) for d in Department.query.all()]

    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                is_admin=form.is_admin.data,
                department_id=form.department_id.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('User created successfully', 'success')
            return redirect(url_for('user.list_users'))
        except IntegrityError:
            db.session.rollback()
            flash('Error creating user: email or username already exists', 'danger')

    return render_template('user/create.html', form=form)


@user_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if not current_user.is_admin and current_user.id != user.id:
        abort(403)

    departments = Department.query.all()
    dept_choices = [(str(d.id), d.name) for d in departments]

    if request.method == 'GET':
        form = UserEditForm(obj=user)
        if current_user.is_admin:
            form.department_id.choices = dept_choices
            form.department_id.data = str(user.department_id) if user.department_id else None
        else:
            del form.is_admin
            del form.department_id
        return render_template('user/edit.html',
                               form=form,
                               user=user,
                               is_admin=current_user.is_admin)

    form = UserEditForm(request.form)

    if current_user.is_admin:
        form.department_id.choices = dept_choices
        form.is_admin.data = request.form.get('is_admin') == 'y'
        if 'department_id' in request.form:
            form.department_id.data = request.form['department_id']

    if form.validate():
        try:
            user.username = form.username.data
            user.email = form.email.data

            if form.password.data:
                user.set_password(form.password.data)

            if current_user.is_admin:
                user.is_admin = form.is_admin.data
                user.department_id = int(form.department_id.data) if form.department_id.data else None

            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('user.list_users'))

        except ValueError:
            db.session.rollback()
            flash('Invalid department ID', 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already exists', 'danger')
    else:
        flash('Please correct the form errors', 'danger')

    return render_template('user/edit.html',
                           form=form,
                           user=user,
                           is_admin=current_user.is_admin)


@user_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot delete yourself', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')

    return redirect(url_for('user.list_users'))
