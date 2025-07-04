from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SelectField,
    IntegerField,
    DateTimeField
)
from wtforms.validators import (
    DataRequired,
    Length,
    EqualTo,
    ValidationError,
    Optional,
    NumberRange
)
from app.models import User, Department
import re
from datetime import datetime, timedelta


def validate_email(form, field):
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', field.data):
        raise ValidationError('Invalid email address')


class BaseUserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        validate_email
    ])

    def validate_username(self, field):
        user = getattr(self, '_user', None)
        if user and User.query.filter(
                User.username == field.data,
                User.id != user.id
        ).first():
            raise ValidationError('Username already taken')

    def validate_email(self, field):
        user = getattr(self, '_user', None)
        if user and User.query.filter(
                User.email == field.data,
                User.id != user.id
        ).first():
            raise ValidationError('Email already in use')


class UserCreateForm(BaseUserForm):
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])
    is_admin = BooleanField('Is Admin')
    department_id = SelectField('Department', coerce=int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]


class UserUpdateForm(BaseUserForm):
    password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        Optional(),
        EqualTo('password', message='Passwords must match')
    ])
    is_admin = BooleanField('Is Admin')
    department_id = SelectField('Department', coerce=int)

    def __init__(self, *args, edit_profile=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = kwargs.get('obj')
        self._edit_profile = edit_profile
        self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]

        if edit_profile:
            del self.is_admin
            del self.department_id


class DepartmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')


class APIConfigForm(FlaskForm):
    name = StringField('Configuration Name', validators=[DataRequired()])
    base_url = StringField('Base URL', validators=[DataRequired()])
    secret_key = StringField('Secret Key', validators=[DataRequired()])
    verify_ssl = BooleanField('Verify SSL')
    is_default = BooleanField('Set as default')


class APISelectForm(FlaskForm):
    config = SelectField('Select Configuration', coerce=int)


class MySQLQueryForm(FlaskForm):
    start_date = DateTimeField(
        'Start Date',
        validators=[DataRequired()],
        format='%Y-%m-%d %H:%M:%S',
        default=datetime.now().replace(day=1, hour=0, minute=0, second=0)
    )
    end_date = DateTimeField(
        'End Date',
        validators=[DataRequired()],
        format='%Y-%m-%d %H:%M:%S',
        default=(datetime.now().replace(day=28) + timedelta(days=4)).replace(hour=23, minute=59, second=59)
    )
    client_id = IntegerField(
        'Client ID',
        validators=[
            DataRequired(),
            NumberRange(min=1, message='Client ID must be positive')
        ]
    )
