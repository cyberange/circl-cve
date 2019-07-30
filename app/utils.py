# -*- coding: utf-8 -*-

from functools import wraps
import os
import gnupg
import redis as redisdb
from flask import render_template, abort
from flask_login import current_user
from flask_mail import Message, Mail
from flask_pymongo import PyMongo

import models


def send_email(to, subject, template, **kwargs):
    msg = Message(subject, recipients=[to], sender=os.getenv('DEFAULT_MAIL_SENDER'))
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    return mail.send(msg)


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    return permission_required(models.Permission.ADMINISTER)(f)

gpg = gnupg.GPG(homedir=os.getenv('GPG_DIR'))
redis = redisdb.StrictRedis(host=os.getenv('REDIS_HOST'),
                            port=os.getenv('REDIS_PORT'),
                            db=os.getenv('REDIS_DB'))
mongo = PyMongo()
mail = Mail()
