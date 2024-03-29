#!/usr/bin/env python2
# -*-coding:UTF-8 -*

from datetime import datetime

from flask import current_app
from sqlalchemy import UniqueConstraint
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin
from flask_scrypt import generate_random_salt, generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

db = SQLAlchemy()


class Permission(object):
    DEFAULT = 0x01
    CPE_NOTIFY = 0x02
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.DEFAULT, True),
            'Validated_User': (Permission.CPE_NOTIFY, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    fulltxt = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    vendor = db.Column(db.String(64), index=True, nullable=False)
    product = db.Column(db.String(64), index=True, nullable=False)
    version = db.Column(db.String(64), nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'vendor', 'product', 'version'),)


class FullTextNotification(db.Model):
    __tablename__ = 'fulltextnotifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fullnotif = db.Column(db.String(64), index=True, nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'fullnotif'),)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(512))
    password_salt = db.Column(db.String(128))
    affiliation = db.Column(db.String(64), nullable=True)
    pgp = db.Column(db.Text, nullable=True)
    fingerprint = db.Column(db.String(64), nullable=True)
    confirmed = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    notification = db.relationship('Notification', backref='user', cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['PORTAL_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
                self.confirmed = "1"
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_salt = generate_random_salt()
        self.password_hash = generate_password_hash(password, self.password_salt)

    def verify_password(self, password):
        return check_password_hash(str(password), str(self.password_hash), str(self.password_salt))

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        user = User.query.get_or_404(data.get('confirm'))
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        db.session.commit()
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        user = User.query.get_or_404(data.get('confirm'))
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        return True
