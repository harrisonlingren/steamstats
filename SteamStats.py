import os, re, requests
from flask import Flask, request, redirect, render_template, abort, jsonify, session, g
from flask_openid import OpenID
from User import User

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': 2592000,
    'DEBUG': True
})

oid = OpenID(app)

@app.route('/')
def index():
    if 'user_id' in session:
        user_logged_in = True
        if session['user_id'] == None:
            return render_template('login.jinja2', user_logged_in=False)
        else:
            UserInfo = User(session['user_id'])
            return render_template('index.jinja2', user_logged_in=True, username=UserInfo.username, avatar=UserInfo.avatar, timeCreated=UserInfo.time_created)
    else:
        return render_template('login.jinja2', user_logged_in=False)
    

# login flow
@app.route('/login')
@oid.loginhandler
def login():
    return oid.try_login('https://steamcommunity.com/openid')

@oid.after_login
def create_or_login(auth):
    _steam_re = re.compile('steamcommunity.com/openid/id/(.*?)$')
    match = _steam_re.search(auth.identity_url)
    g.user = {}
    steamid = match.group(1)
    g.user['id'] = steamid
    session['user_id'] = steamid
    user_logged_in = True
    return redirect('/')


# pull logged in User from cookie
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = session['user_id']


# logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(oid.get_next_url())


# 404 handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.jinja2'), 404

if __name__ == '__main__':
    app.run()