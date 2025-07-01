import re
from typing import Any, Optional, TypeVar
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError, Optional as Opt

from app.models.department import Department
from app.models.user import User

# Тип для объекта пользователя
UserObj = TypeVar('UserObj', bound=User)


def validate_email(_form: FlaskForm, field: StringField) -> None:
    """Кастомный валидатор email без зависимости от email_validator"""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, field.data):
        raise ValidationError('Введите корректный email адрес')


class APIConfigForm(FlaskForm):
    name = StringField('Configuration Name', validators=[DataRequired()])
    base_url = StringField('Base URL', validators=[DataRequired()])
    secret_key = StringField('Secret Key', validators=[DataRequired()])
    verify_ssl = BooleanField('Verify SSL')
    is_default = BooleanField('Set as default', default=False)


class APISelectForm(FlaskForm):
    config = SelectField('Select Configuration', coerce=int)


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), validate_email])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password')]
    )
    is_admin = BooleanField('Is Admin')
    department_id = SelectField('Department', coerce=int)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.all()]


class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), validate_email])
    password = PasswordField('New Password', validators=[Length(min=6)])
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[EqualTo('password')]
    )
    is_admin = BooleanField('Is Admin')
    department_id = SelectField('Department', coerce=int, validators=[Opt()])

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._obj: Optional[User] = kwargs.pop('obj', None)
        super().__init__(*args, **kwargs)

        # Заполняем данные формы из объекта пользователя
        if self._obj:
            self.username.data = self._obj.username
            self.email.data = self._obj.email
            self.is_admin.data = self._obj.is_admin
            if hasattr(self._obj, 'department_id'):
                self.department_id.data = self._obj.department_id

        # Заполняем choices для department_id
        if current_user.is_authenticated and current_user.is_admin:
            self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
        else:
            self.department_id.choices = []

    def validate_username(self, field: StringField) -> None:
        if self._obj is None:
            return

        if User.query.filter(
                User.username == field.data,
                User.id != self._obj.id
        ).first():
            raise ValidationError('This username is already taken')

    def validate_email(self, field: StringField) -> None:
        if self._obj is None:
            return

        if User.query.filter(
                User.email == field.data,
                User.id != self._obj.id
        ).first():
            raise ValidationError('This email is already in use')


class UserProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), validate_email])
    password = PasswordField('New Password', validators=[Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[EqualTo('password')]
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._obj: Optional[User] = kwargs.pop('obj', None)
        super().__init__(*args, **kwargs)

        if self._obj:
            self.username.data = self._obj.username
            self.email.data = self._obj.email

    def validate_username(self, field: StringField) -> None:
        if self._obj is None:
            return

        if User.query.filter(
                User.username == field.data,
                User.id != self._obj.id
        ).first():
            raise ValidationError('Username already taken')

    def validate_email(self, field: StringField) -> None:
        if self._obj is None:
            return

        if User.query.filter(
                User.email == field.data,
                User.id != self._obj.id
        ).first():
            raise ValidationError('Email already in use')


class AdminProfileForm(UserProfileForm):
    department_id = SelectField('Department', coerce=int, validators=[Opt()])

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]

        if self._obj and hasattr(self._obj, 'department_id'):
            self.department_id.data = self._obj.department_id


class DepartmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
