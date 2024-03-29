# -*- coding: utf-8 -*-
import syslog

from flask import Blueprint, flash, redirect, url_for, escape, render_template, request
from flask_login import login_required, current_user, login_user, logout_user

import models
import form_class
# from utils import send_email, gpg
from utils import gpg

user_blueprint = Blueprint('user', __name__)


@user_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    form = form_class.RegistrationForm()
    if form.validate_on_submit():
        ki = gpg.import_keys(form.pgp.data)
        if not ki.fingerprints:
            fingerp = "--- NO VALID PGP ---"
        else:
            fingerp = ki.fingerprints[0]
        user = models.User(email=escape(form.email.data),
                           name=escape(form.name.data),
                           affiliation=escape(form.affiliation.data),
                           pgp=escape(form.pgp.data),
                           password=form.password.data,
                           fingerprint=fingerp,
                           confirmed=True)
        models.db.session.add(user)
        models.db.session.commit()
        syslog.syslog(syslog.LOG_NOTICE, "New user registered: " + form.email.data)
        # token = user.generate_confirmation_token()
        # send_email(user.email,
        #            'CVE-PORTAL -- Account Confirmation',
        #            '/emails/confirm',
        #            user=user,
        #            token=token)
        # flash('A confirmation email has been sent to you by email.', 'info')
        return redirect('/user/login')
    else:
        if form.email.data is not None:
            pass
            # syslog.syslog(syslog.LOG_ERR, "Registering Failed: Email: " + form.email.data + " Name: " + form.name.data + " Affiliation: " + form.affiliation.data)

    return render_template("auth/register.html", form=form)


@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = form_class.LoginForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('You are now logged', 'success')
            syslog.syslog(syslog.LOG_INFO, "User Logged: " + form.email.data)
            return redirect(request.args.get("next") or url_for("main.index"))
        flash('Wrong email/password', 'danger')
        syslog.syslog(syslog.LOG_ERR, "User Login Failed: " + form.email.data)
    return render_template('auth/login.html', form=form)


@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect('/')


@user_blueprint.route('/confirm')
@login_required
def resend_confirmation():
    flash('This feature has not been implemented.', 'info')
    return redirect(url_for('main.index'))
    # token = current_user.generate_confirmation_token()
    # send_email(current_user.email,
    #            'CVE-PORTAL -- Account Confirmation',
    #            '/emails/confirm',
    #            user=current_user,
    #            token=token)
    # syslog.syslog(syslog.LOG_WARNING, "User Resend a Confirmation Email to: " + current_user.email)
    # flash('A new confirmation email has been sent to you by email.', 'info')
    # return redirect(url_for('main.index'))


@user_blueprint.route('/confirm/<token>')
def confirm(token):
    if not current_user.is_anonymous():
        if current_user.confirmed:
            return redirect(url_for('main.index'))
    else:
        if current_user.confirm(token):
            # syslog.syslog(syslog.LOG_INFO, "User Confirmed Account: " + current_user.email)
            flash('You have confirmed your account. Thanks!', 'success')
        else:
            # syslog.syslog(syslog.LOG_ERR, "User Confirmed Failed invalid/expired link: " + current_user.email)
            flash('The confirmation link is invalid or has expired.', 'warning')
        return redirect(url_for('main.index'))


@user_blueprint.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@user_blueprint.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = form_class.ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            models.db.session.add(current_user)
            models.db.session.commit()
            flash('Your password has been updated.', 'info')
            syslog.syslog(syslog.LOG_INFO, "User changed his password: " + current_user.email)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.', 'danger')
    return render_template("auth/change_password.html", form=form)


@user_blueprint.route('/reset_pwd', methods=['GET', 'POST'])
def password_reset_request():
    flash('This feature has not been implemented.', 'info')
    return redirect(url_for('main.index'))
    # if not current_user.is_anonymous():
    #     return redirect(url_for('main.index'))
    # form = form_class.PasswordResetRequestForm()
    # if form.validate_on_submit():
    #     user = models.User.query.filter_by(email=form.email.data).first()
    #     if user:
    #         token = user.generate_reset_token()
    #         send_email(user.email,
    #                    'CVE-PORTAL -- Reset Password Request',
    #                    '/emails/password_reset',
    #                    user=user,
    #                    token=token,
    #                    next=request.args.get('next'))
    #         # syslog.syslog(syslog.LOG_WARNING, "User password reset request is asked: " + current_user.email)
    #         flash('An email with instructions to reset your password has been sent to you.', 'info')
    #         return redirect(url_for('user.login'))
    # return render_template('auth/reset_password.html', form=form)


@user_blueprint.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    flash('This feature has not been implemented.', 'info')
    return redirect(url_for('main.index'))
    # form = form_class.ChangeEmailForm()
    # if form.validate_on_submit():
    #     if current_user.verify_password(form.password.data):
    #         new_email = escape(form.email.data)
    #         token = current_user.generate_email_change_token(new_email)
    #         send_email(new_email,
    #                    'CVE-PORTAL -- Confirm your email address',
    #                    '/emails/change_email',
    #                    user=current_user,
    #                    token=token)
    #         syslog.syslog(syslog.LOG_WARNING,
    #                       "User as requested an email change: Old:" + current_user.email + " New: " + form.email.data)
    #         flash('An email with instructions to confirm your new email address has been sent to you.', 'info')
    #         return redirect(url_for('main.index'))
    #     else:
    #         flash('Invalid email or password.', 'danger')
    # return render_template("auth/change_email.html", form=form)


@user_blueprint.route('/change_pgp', methods=['GET', 'POST'])
@login_required
def change_pgp():
    form = form_class.ChangePGPForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            ki = gpg.import_keys(form.pgp.data)
            if not ki.fingerprints:
                fingerp = "--- NO VALID PGP ---"
            else:
                fingerp = ki.fingerprints[0]
            current_user.pgp = form.pgp.data
            current_user.fingerprint = fingerp
            models.db.session.add(current_user)
            models.db.session.commit()
            flash('Your PGP key has been updated.', 'info')
            syslog.syslog(syslog.LOG_INFO, "User Changed his PGP: " + current_user.email)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.', 'danger')
    return render_template("auth/change_pgp.html", form=form)


@user_blueprint.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        syslog.syslog(syslog.LOG_INFO, "User e-mail updated: " + current_user.email)
        flash('Your email address has been updated.', 'success')
    else:
        syslog.syslog(syslog.LOG_ERR, "Email change: Invalid link request: " + current_user.email)
        flash('Invalid request.', 'warning')
    return redirect(url_for('main.index'))


@user_blueprint.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous():
        return redirect(url_for('main.index'))
    form = form_class.PasswordResetForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.', 'success')
            return redirect(url_for('user.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@user_blueprint.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    return render_template('user.html')
