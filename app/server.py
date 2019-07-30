#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import logging
import syslog
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user
from flask_script import Manager

import models
from utils import mail
from views.main import main_blueprint
from views.notif import notif_blueprint, mongo
from views.user import user_blueprint

########################################################################
####################### APP INIT & CONFIG ##############################
########################################################################

app = Flask(__name__)
app.debug=True
app.register_blueprint(main_blueprint)
app.register_blueprint(notif_blueprint, url_prefix='/notif')
app.register_blueprint(user_blueprint, url_prefix='/user')

# Login_manager (session)
login_manager = LoginManager(app)
login_manager.session_protection = 'strong'
login_manager.anonymous_user = models.AnonymousUser

mail.init_app(app)
manager = Manager(app)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# app.config['SERVER_NAME'] = "www.circl.lu:443"
# app.config['APPLICATION_ROOT'] = '/cve-portal'
# app.config['WTF_CSRF_ENABLED'] = True

# SMTP email config #
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = True if os.getenv('MAIL_USE_TLS') else False
app.config['DEFAULT_MAIL_SENDER'] = os.getenv('DEFAULT_MAIL_SENDER')

# Super Admin #
app.config['PORTAL_ADMIN'] = os.getenv('PORTAL_ADMIN')

# MONGO  #
mongo_host = os.getenv('MONGO_HOST')
mongo_port = os.getenv('MONGO_PORT')
mongo_dbname = os.getenv('MONGO_DB')
app.config['MONGO_URI']= "mongodb://"+mongo_host+":"+mongo_port+"/"+mongo_dbname
# app.config['MONGO_DBNAME'] = 
mongo.init_app(app)

# SYSLOG #
syslog.openlog(str(os.getenv('SYSLOG_FILE')), logoption=syslog.LOG_PID, facility=syslog.LOG_USER)

# SQLAlchemy #
db_type = os.getenv('DB_TYPE')
db_user = os.getenv('DB_USER')
db_pwd = os.getenv('DB_PASS')
db_hostname = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = db_type + '://' + db_user + ':' + db_pwd + '@' + db_hostname + '/' + db_name
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
models.db.init_app(app)


########################################################################
############################# REQUEST HANDLERS #########################
########################################################################

req_endpoint = ['unconfirmed', 'logout', 'confirm', 'index', 'resend_confirmation']


# Logging stderr output
@app.before_first_request
def setup_logging():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint not in req_endpoint:
            return redirect(url_for('unconfirmed'))


@app.teardown_appcontext
def shutdown_session(exception=None):
    models.db.session.remove()


@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))


########################################################################
############################# ERROR HANDLERS ###########################
########################################################################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.errorhandler(401)
def unauthorized(e):
    return render_template('401.html'), 401


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


if __name__ == "__main__":
    manager.run()
