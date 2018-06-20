import os, re, requests
from flask import Flask, request, redirect, render_template, abort, session, g, jsonify, make_response
from flask_openid import OpenID
from threading import Thread

from User import User

# flag for GetLibrary thread
GET_LIB_WORKING = False

# cache user info in memory
user_info_store = {}

# cache game info in memory
user_info_store = {}

# init app
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

# Results Page
@app.route('/results')
def results():
    return render_template('results.jinja2')

# Get user data by steam_id
@app.route('/user/<steam_id>')
def GetUserInfo(steam_id):
    global GET_LIB_WORKING

    def GetGames(user):
        global GET_LIB_WORKING

        user.GetLibrary()
        GET_LIB_WORKING = False

    if steam_id in user_info_store:
        if (not GET_LIB_WORKING) and len(user_info_store[steam_id].library) < 1:
            thread = Thread(target=GetGames, args=[user_info_store[steam_id]])
            thread.start()
            GET_LIB_WORKING = True
            return make_response('Collecting game library...', 202)

        elif GET_LIB_WORKING:
            return make_response('Collecting game library...', 202)
            
        elif not GET_LIB_WORKING:
            serialized_user = jsonify(user_info_store[steam_id].asdict())
            return make_response(serialized_user, 200)
        
        else:
            return make_response('Error: There was a problem completing your request. Check your query and try again.', 400)
        
    else:
        return make_response(jsonify({'error': 'User not found'}), 404)

@app.route('/user/<steam_id>/count')
def GetUserGameCount(steam_id):
    if steam_id in user_info_store:
        result = {'total': user_info_store[steam_id].gamecount, 'loaded': len(user_info_store[steam_id].library)}
        if result['total'] > result['loaded']:
            return make_response(jsonify(result), 202)
        else:
            return make_response(jsonify(result), 200)
    else:
        return make_response(jsonify({'error': 'User not found'}), 404)

if __name__ == '__main__':
    app.run()
