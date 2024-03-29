#!/usr/bin/env python2
# -*-coding:UTF-8 -*

# WebForms #
from flask_wtf import Form
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms import PasswordField, ValidationError, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Regexp, EqualTo, Optional

import models


class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    name = StringField('Name',
                       validators=[DataRequired(),
                                   Length(1, 64),
                                   Regexp('^[A-Za-z][A-Za-z0-9_. ]*$', 0,
                                          'Name must have only letters, \
                                          numbers, dots or underscores.')])
    email = StringField('Email',
                        validators=[DataRequired(),
                                    Email(),
                                    Length(1, 64)])
    password = PasswordField('Password',
                             validators=[DataRequired(),
                                         EqualTo('password2',
                                                 message='Passwords must match.'),
                                         Length(min=8,
                                                message='minimum password length: 8')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    affiliation = StringField('Affiliation', validators=[Optional()])
    pgp = TextAreaField('PGP Key', validators=[Optional()])
    submit = SubmitField('Go !')

    def validate_email(self, field):
        if models.User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if models.User.query.filter_by(name=field.data).first():
            raise ValidationError('Name already in use.')

    def validate_pgp(self, field):
        if models.User.query.filter_by(pgp=field.data).first():
            raise ValidationError('PGP already in use.')


class UpdateUserForm(Form):
    id = HiddenField()
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Name',
                       validators=[DataRequired(),
                                   Length(1, 64),
                                   Regexp('^[A-Za-z][A-Za-z0-9_. ]*$', 0,
                                          'Username must have only letters, \
                                          numbers, dorts or underscores.')])
    email = StringField('Email',
                        validators=[DataRequired(),
                                    Email(),
                                    Length(1, 64)])
    affiliation = StringField('Affiliation', validators=[Optional()])
    pgp = TextAreaField('PGP Key', validators=[Optional()])
    submit = SubmitField('Update')

    def __init__(self, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in models.Role.query.order_by(models.Role.name).all()]


class DeleteUserForm(Form):
    id = HiddenField(validators=[DataRequired()])
    deltrigger = HiddenField('Deltrigger', validators=[DataRequired()])
    name = StringField('Name')
    email = StringField('Email')
    affiliation = StringField('Affiliation')
    submit = SubmitField('Delete')


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(),
        EqualTo('password2', message='Passwords must match'),
        Length(min=8, message='minimum password length: 8')])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])
    submit = SubmitField('Update password')


class PasswordResetRequestForm(Form):
    email = StringField('Email',
                        validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email',
                        validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('New Password',
                             validators=[DataRequired(),
                                         EqualTo('password2',
                                                 message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if models.User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangeEmailForm(Form):
    email = StringField('New Email',
                        validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update e-mail address')

    def validate_email(self, field):
        if models.User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangePGPForm(Form):
    pgp = TextAreaField('New PGP Key', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update PGP key')
