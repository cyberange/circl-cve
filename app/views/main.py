# -*- coding: utf-8 -*-

import syslog

from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, escape
from flask_login import login_required, current_user
from sqlalchemy import desc
import os
import form_class
import models
from utils import admin_required, gpg

main_blueprint = Blueprint('main', __name__)


@main_blueprint.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@main_blueprint.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_home():
    newform = form_class.RegistrationForm()
    updateform = form_class.UpdateUserForm()
    deleteform = form_class.DeleteUserForm()

    if deleteform.validate_on_submit():
        if deleteform.id.data != '1':
            user = models.User.query.filter_by(id=deleteform.id.data).first()
            models.db.session.delete(user)
            models.db.session.commit()
            flash('User successfully deleted', 'success')
            syslog.syslog(syslog.LOG_CRIT, "Admin: " + current_user.email + " deleted User: " + user.email)
        else:
            flash("Sorry but you just can't delete this admin.", 'danger')
            syslog.syslog(syslog.LOG_ALERT, "User wanted to delete admin" + current_user.email)
        return redirect(url_for('main.admin_home'))

    elif newform.validate_on_submit():
        ki = gpg.import_keys(newform.pgp.data)
        if not ki.fingerprints:
            fingerp = "--- NO VALID PGP ---"
        else:
            fingerp = ki.fingerprints[0]
        user = models.User(email=escape(newform.email.data),
                           name=escape(newform.name.data),
                           affiliation=escape(newform.affiliation.data),
                           pgp=newform.pgp.data,
                           password=newform.password.data,
                           fingerprint=fingerp,
                           confirmed=True)

        models.db.session.add(user)
        models.db.session.commit()
        syslog.syslog(syslog.LOG_WARNING, "Admin: " + current_user.email + " created User: " + user.email)
        flash('User successfully created.', 'success')
        return redirect(url_for('main.admin_home'))

    elif updateform.validate_on_submit():
        ki = gpg.import_keys(updateform.pgp.data)
        if not ki.fingerprints:
            fingerp = "--- NO VALID PGP ---"
        else:
            fingerp = ki.fingerprints[0]
        user = models.User.query.filter_by(id=updateform.id.data).first()
        user.name = escape(updateform.name.data)
        user.affiliation = escape(updateform.affiliation.data)
        user.fingerprint = fingerp
        user.pgp = updateform.pgp.data

        if updateform.id.data != '1':
            listemail = []
            for user in models.User.query.all():
                listemail.append(user.email)
            if updateform.email.data not in listemail or updateform.email.data == models.User.query.filter_by(
                    id=updateform.id.data).first().email:
                user.email = escape(updateform.email.data)
                user.confirmed = updateform.confirmed.data
                user.role = models.Role.query.get(updateform.role.data)
            else:
                syslog.syslog(syslog.LOG_ERR,
                              "Admin: " + current_user.email + " Tried to assign existing email to user: " + user.email)
                flash('Email already existing', 'warning')
                return redirect(url_for('main.admin_home'))
        else:
            user.role = models.Role.query.get('1')
            user.email = os.getenv('PORTAL_ADMIN')
            user.confirmed = True
            syslog.syslog(syslog.LOG_ALERT,
                          "Admin: " + current_user.email + " Tried to remove right of Admin: " + user.email)

        models.db.session.add(user)
        models.db.session.commit()
        syslog.syslog(syslog.LOG_WARNING, "Admin: " + current_user.email + " updated User: " + user.email)
        flash('User successfully updated', 'success')
        return redirect(url_for('main.admin_home'))

    return render_template("admin_home.html",
                           newform=newform,
                           updateform=updateform,
                           deleteform=deleteform)


@main_blueprint.route('/userjson', methods=['GET', 'POST'])
@login_required
@admin_required
def userjson():
    jusers = []
    dic = {}

    limit = request.args.get('limit')
    offset = request.args.get('offset')
    order = request.args.get('order')

    if 'users.' + request.args.get('sort') in models.User.__table__.columns:
        sort = request.args.get('sort')
    else:
        sort = 'name'

    if order == 'desc':
        user_list = models.User.query.order_by(desc(sort)).limit(limit).offset(offset).all()
    else:
        user_list = models.User.query.order_by(sort).limit(limit).offset(offset).all()

    num = models.User.query.count()

    for user in user_list:
        dusers = {'id': user.id,
                  'name': user.name,
                  'email': user.email,
                  'affiliation': user.affiliation,
                  'pgp': user.pgp,
                  'fingerprint': user.fingerprint,
                  'confirmed': user.confirmed,
                  'role_id2': user.role_id,
                  'role_id': (models.Role.query.filter_by(id=user.role_id).first()).name
                  }
        jusers.append(dusers)

    dic['total'] = num
    dic['rows'] = jusers
    return jsonify(dic)
