from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Department
from .forms import UserCreateForm, UserUpdateForm
from sqlalchemy.exc import IntegrityError
from . import user_bp  # Импортируем Blueprint


@user_bp.route('/users')
@login_required
def list_users():
    # Разрешаем просмотр списка всем авторизованным
    users = User.query.all()
    return render_template('user/list.html',
                           users=users,
                           current_user=current_user)  # Явно передаем current_user


@user_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        abort(403)

    form = UserCreateForm()

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
            flash('Username or email already exists', 'danger')

    return render_template('user/create.html', form=form)


@user_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    # Разрешаем:
    # - Админам редактировать любого
    # - Пользователям - только свой профиль
    if not current_user.is_admin and current_user.id != user.id:
        abort(403)

    form = UserUpdateForm(obj=user,
                          edit_profile=not current_user.is_admin)  # Для админов показываем все поля

    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data

            if form.password.data:
                user.set_password(form.password.data)

            if current_user.is_admin:
                user.is_admin = form.is_admin.data
                user.department_id = form.department_id.data

            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('user.list_users'))
        except IntegrityError:
            db.session.rollback()
            flash('Error updating user', 'danger')

    return render_template('user/edit.html', form=form, user=user)


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    form = UserUpdateForm(obj=current_user, edit_profile=True)

    if form.validate_on_submit():
        try:
            current_user.username = form.username.data
            current_user.email = form.email.data

            if form.password.data:
                current_user.set_password(form.password.data)

            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('user.user_profile'))
        except IntegrityError:
            db.session.rollback()
            flash('Error updating profile', 'danger')

    return render_template('user/profile.html', form=form)


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
