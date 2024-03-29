# -*- coding: utf-8 -*-

import cgi
import json
import syslog

from bson import json_util
from datetime import datetime
from flask import Blueprint, request, jsonify, flash, redirect, url_for, escape
from flask_login import login_required, current_user
from flask_pymongo import DESCENDING
from sqlalchemy import desc

import cve_redis
import models
from utils import redis, mongo

notif_blueprint = Blueprint('notif', __name__)


@notif_blueprint.route('/notiftab', methods=['GET', 'POST'])
@login_required
def notiftab():
    jnotif = []
    dic = {}

    limit = request.args.get('limit')
    offset = request.args.get('offset')
    sort = request.args.get('sort')
    order = request.args.get('order')

    if order == 'desc':
        notif_list = models.Notification.query.filter_by(user_id=current_user.id).order_by(desc(sort)).limit(
            limit).offset(offset).all()
    else:
        notif_list = models.Notification.query.filter_by(user_id=current_user.id).order_by(sort).limit(limit).offset(
            offset).all()

    num = models.Notification.query.filter_by(user_id=current_user.id).count()

    for notif in notif_list:
        dnotif = {'id': notif.id,
                  'fulltxt': notif.fulltxt,
                  'vendor': notif.vendor,
                  'product': notif.product,
                  'version': notif.version
                  }
        jnotif.append(dnotif)

    dic['total'] = num
    dic['rows'] = jnotif
    return jsonify(dic)


@notif_blueprint.route('/notifjson', methods=['GET', 'POST'])
@login_required
def notifjson():
    vendors = []
    products = []
    versions = []
    if request.json is not None:
        if request.json['queryvendor'] != "":  # SEARCH BY VENDORS
            vendors = cve_redis.search_vendor(redis, request.json['queryvendor'].lower())
            products = cve_redis.search_vendor_product(redis, request.json['queryproduct'].lower(),
                                                       request.json['queryvendor'].lower())
            versions = cve_redis.product_versions(redis, request.json['queryproduct'].lower())
        elif request.json['queryproduct'] != "":  # SEARCH BY PRODUCTS
            products = cve_redis.search_product(redis, request.json['queryproduct'].lower())
            vendors = cve_redis.get_vendor(redis, request.json['queryproduct'].lower())
            versions = cve_redis.product_versions(redis, request.json['queryproduct'].lower())

    return jsonify({"vendors": vendors,
                    "products": products,
                    "versions": versions})


@notif_blueprint.route('/addnotif', methods=['GET', 'POST'])
@login_required
def addnotif():
    if request.json['allversion'] is True and request.json['allproduct'] is False:
        notification = models.Notification(user_id=current_user.id,
                                           vendor=escape(request.json['queryvendor'].lower()),
                                           product=escape(request.json['queryproduct'].lower()),
                                           version='')

    elif request.json['allproduct'] is True:
        notification = models.Notification(user_id=current_user.id,
                                           vendor=escape(request.json['queryvendor'].lower()),
                                           product='',
                                           version='')
    else:
        notification = models.Notification(user_id=current_user.id,
                                           vendor=escape(request.json['queryvendor'].lower()),
                                           product=escape(request.json['queryproduct'].lower()),
                                           version=escape(request.json['queryversion'].lower()))

    # Checking Integrity Before Insert  #
    if models.Notification.query.filter_by(user_id=notification.user_id,
                                           vendor=notification.vendor,
                                           product=notification.product,
                                           version=notification.version).first() is None:
        models.db.session.add(notification)
        models.db.session.commit()
        flash('Notification Successfully Created.', 'success')
        syslog.syslog(syslog.LOG_DEBUG, "New notification created by: " + current_user.email)
        return redirect(url_for("notif.notiftab"))

    else:
        flash('Notification Already existing.', 'warning')
        syslog.syslog(syslog.LOG_ERR, "Notification Already existing: " + current_user.email)
        return redirect(url_for("notif.notiftab"))


@notif_blueprint.route('/delnotif', methods=['GET', 'POST'])
@login_required
def delnotif():
    row = models.Notification.query.filter_by(id=request.json).first()
    models.db.session.delete(row)
    models.db.session.commit()
    flash('Notification removed ', 'info')
    syslog.syslog(syslog.LOG_DEBUG, "Notification deleted: " + current_user.email)
    return redirect(url_for("notif.notiftab"))


@notif_blueprint.route('/checknotif', methods=['GET', 'POST'])
@login_required
def checknotif():
    if request.json["product"] == '':
        req = ':' + request.json['vendor'] + ':'
    else:
        req = request.json["vendor"] + ':' + request.json["product"] + ':' + request.json["version"]

    tab = []
    keytab = ['summary']
    for cves in mongo.db.cves.find({'vulnerable_configuration': {'$regex': req}}).sort("Modified", DESCENDING):
        dic = {}
        for key, value in cves.items():
            if key in keytab:
                dic[key] = cgi.escape(value, quote=True)
            else:
                if isinstance(value, datetime):
                    value = str(value)
                dic[key] = value
        tab.append(dic)
    return json.dumps(tab, sort_keys=True, default=json_util.default)


@notif_blueprint.route('/searchnotif', methods=['GET', 'POST'])
@login_required
def searchnotif():
    notification = models.Notification(user_id=current_user.id,
                                       fulltxt=True,
                                       vendor=escape(request.json['searchquery']),
                                       product='',
                                       version='')
    # Checking Integrity Before Insert  #
    if models.Notification.query.filter_by(user_id=notification.user_id,
                                           vendor=notification.vendor,
                                           fulltxt=notification.fulltxt).first() is None:
        models.db.session.add(notification)
        models.db.session.commit()
        flash('Notification Successfully Created.', 'success')
        syslog.syslog(syslog.LOG_DEBUG, "New notification created by: " + current_user.email)
        return redirect(url_for("notif.notiftab"))
    else:
        flash('Notification Already existing.', 'warning')
        syslog.syslog(syslog.LOG_ERR, "Notification Already existing: " + current_user.email)
        return redirect(url_for("notif.notiftab"))
