import os, re, requests
from flask import Flask, request, redirect, render_template, abort, session, g, jsonify, make_response
from flask_openid import OpenID
from threading import Thread

from User import User

# init app
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': 2592000,
    'DEBUG': True
})

oid = OpenID(app)


### data caches
# cache user info in memory
user_info_store = {}

# cache game info in memory
game_info_store = {}

with app.app_context():
    ### template responses
    # pending library
    RESP_LIBRARY_PENDING = make_response(jsonify({'message':'Collecting game library...'}), 202)

    # user not found
    RESP_USER_NOT_FOUND = make_response(jsonify({'error':'User not found'}), 404)

### flags
# GetLibrary thread
GET_LIB_WORKING = False

# LoadGamesInStore thread
LOAD_GAMES_WORKING = False


### ROUTES below
# -----------------------

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

# Profile Page (for specific user)
@app.route('/profile/<steam_id>')
def profileById(steam_id):
    if steam_id not in user_info_store:
        user_info_store[steam_id] = User(steam_id)
    
    user_info = user_info_store[steam_id]
    return render_template('profile.jinja2', steam_id=steam_id, username=user_info.username, time_created=user_info.time_created, avatar=user_info.avatar)


# Search results Page
@app.route('/results')
def results():

    # get search params
    keyword = request.args.get('q')
    results = []

    for (steam_id, user) in user_info_store.items():
        if keyword in user.username:
            results.append({'url': '/profile/' + steam_id, 'text': user.username})
    
    for (app_id, game) in game_info_store.items():
        if keyword in game.title or keyword in game.description or keyword in game.genre:
            results.append({'url': 'https://store.steampowered.com/app/' + app_id, 'text': game.title})

    print('search results:', results)
    return render_template('results.jinja2', results=results)


# Friends Page
@app.route('/friends')
def friends():
    return render_template('friends.jinja2')
  

# Get user data by steam_id
@app.route('/user/<steam_id>')
def GetUserInfo(steam_id):
    global GET_LIB_WORKING

    if steam_id in user_info_store:
        if (not GET_LIB_WORKING) and len(user_info_store[steam_id].library) < 1:
            thread = Thread(target=GetGames, args=[user_info_store[steam_id]])
            thread.start()
            GET_LIB_WORKING = True
            return RESP_LIBRARY_PENDING

        elif GET_LIB_WORKING:
             return RESP_LIBRARY_PENDING
            
        elif not GET_LIB_WORKING:
            serialized_user = jsonify(user_info_store[steam_id].asdict())
            return make_response(serialized_user, 200)
        
        else:
            return make_response('Error: There was a problem completing your request. Check your query and try again.', 400)
        
    else:
        return RESP_USER_NOT_FOUND


# Get # of games in user's library
#   (specifically: total games vs. loaded games.
#   This endpoint is used to poll load progress)
@app.route('/user/<steam_id>/count')
def GetUserGameCount(steam_id):
    global GET_LIB_WORKING
    if steam_id in user_info_store:
        result = {'total': user_info_store[steam_id].gamecount, 'loaded': len(user_info_store[steam_id].library)}
        if GET_LIB_WORKING and result['total'] > result['loaded']:
            return make_response(jsonify(result), 202)

        else:
            return make_response(jsonify(result), 200)

    else:
        return RESP_USER_NOT_FOUND


# Get user library directly
@app.route('/user/<steam_id>/games')
def GetUserGameLibrary(steam_id):
    if steam_id in user_info_store:
        if not GET_LIB_WORKING:
            resp = jsonify(user_info_store[steam_id].library)
            return make_response(resp, 200)

        else:
             return RESP_LIBRARY_PENDING

    else:
        return RESP_USER_NOT_FOUND


### HELPER functions below
# ------------------------

def GetGames(user):
    global GET_LIB_WORKING

    user.GetLibrary()
    GET_LIB_WORKING = False

    if not LOAD_GAMES_WORKING:
        thread = Thread(target=LoadGamesInStore, args=[user])
        thread.start()


# Load previously fetched games into memory
def LoadGamesInStore(user):
    for (app_id, game) in user.library.items():
        if game['game'].id not in game_info_store:
            game_info_store[app_id] = game['game']


# Run the thing
if __name__ == '__main__':
    app.run()
