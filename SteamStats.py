import os, re, requests
from flask import Flask, request, redirect, render_template, abort, session, g, jsonify, make_response
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

# cache user info in memory
user_info_store = {}

@app.route('/')
def index():
    if 'user_id' in session:
        if session['user_id'] == None:
            return render_template('login.jinja2')
        else:
            steam_id = session['user_id']
            if steam_id not in user_info_store:
                user_info_store[steam_id] = User(steam_id)
            user_info = user_info_store[session['user_id']]
            return render_template('index.jinja2', steam_id=steam_id, username=user_info.username, time_created=user_info.time_created, avatar=user_info.avatar)
    else:
        return render_template('login.jinja2')

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
    steam_id = match.group(1)
    g.user['id'] = steam_id
    session['user_id'] = steam_id
    if steam_id not in user_info_store:
        user_info_store[steam_id] = User(steam_id)
    return redirect('/profile')

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
    return redirect('/')


# 404 handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.jinja2'), 404

# Profile Page
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/')
    else:
        steam_id = session['user_id']
        if steam_id not in user_info_store:
                user_info_store[steam_id] = User(steam_id)
        user_info = user_info_store[steam_id]
        return render_template('profile.jinja2', steam_id=steam_id, username=user_info.username, time_created=user_info.time_created, avatar=user_info.avatar)


# Send user data by steam_id
@app.route('/user/<steam_id>')
def GetUserInfo(steam_id):
    if steam_id in user_info_store:
        user_info = user_info_store[ steam_id ]

        if len(user_info.library) < 1:
            user_info_store[steam_id].library = user_info.GetLibrary()

        serialized_user = jsonify(user_info.asdict())
        return make_response(serialized_user, 200)

    else:
        return abort(404)

if __name__ == '__main__':
    app.run()