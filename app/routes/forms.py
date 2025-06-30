from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, validators
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError, Optional
from app.models.user import User
from flask_login import current_user
from app.models.department import Department
import re


def validate_email(form, field):
    """Кастомный валидатор email без зависимости от email_validator"""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, field.data):
        raise ValidationError('Введите корректный email адрес')


class APIConfigForm(FlaskForm):
    name = StringField('Configuration Name', validators=[validators.DataRequired()])
    base_url = StringField('Base URL', validators=[validators.DataRequired()])
    secret_key = StringField('Secret Key', validators=[validators.DataRequired()])
    verify_ssl = BooleanField('Verify SSL')
    is_default = BooleanField('Set as default', default=False)  # Добавляем default=False


class APISelectForm(FlaskForm):
    config = SelectField('Select Configuration', coerce=int)


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), validate_email])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Is Admin')
    department_id = SelectField('Department', coerce=int)


class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), validate_email])
    password = PasswordField('New Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[EqualTo('password')])
    is_admin = BooleanField('Is Admin')
    department_id = SelectField('Department', coerce=int, validators=[Optional()])

    def __init__(self, *args, **kwargs):
        self._obj = kwargs.get('obj')  # Сохраняем редактируемый объект
        super(UserEditForm, self).__init__(*args, **kwargs)

        if current_user.is_authenticated and current_user.is_admin:
            self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
        else:
            self.department_id.choices = []

    def validate_username(self, field):
        if self._obj and User.query.filter(
                User.username == field.data,
                User.id != self._obj.id
        ).first():
            raise ValidationError('This username is already taken')

    def validate_email(self, field):
        if self._obj and User.query.filter(
                User.email == field.data,
                User.id != self._obj.id
        ).first():
            raise ValidationError('This email is already in use')


class UserProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), validate_email])
    password = PasswordField('New Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[EqualTo('password')])

    def __init__(self, *args, **kwargs):
        self._obj = kwargs.get('obj')
        super(UserProfileForm, self).__init__(*args, **kwargs)

    def validate_username(self, field):
        if self._obj and User.query.filter(User.username == field.data, User.id != self._obj.id).first():
            raise ValidationError('Username already taken')

    def validate_email(self, field):
        if self._obj and User.query.filter(User.email == field.data, User.id != self._obj.id).first():
            raise ValidationError('Email already in use')


class AdminProfileForm(UserProfileForm):
    department_id = SelectField('Department', coerce=int, validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(AdminProfileForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]


class DepartmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
