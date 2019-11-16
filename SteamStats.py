import decimal, os, re, requests
from flask import Flask, request, redirect, render_template, abort, session, g, jsonify, make_response
from flask_openid import OpenID
from threading import Thread
from pymongo import MongoClient
from User import User
from Game import Game

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

# setup mongo client
# connect to mongo and get collection
DB_CONN_STR = os.getenv('DB_CONN_STR')
DB_NAME = os.getenv('DB_NAME')
GAMES_COL_NAME = os.getenv('GAMES_COL_NAME')

_mongoclient = MongoClient(DB_CONN_STR)
_SS_DB = _mongoclient[DB_NAME]
_GAMES = _SS_DB[GAMES_COL_NAME]

with app.app_context():
    ### template responses
    # pending library
    RESP_LIBRARY_PENDING = make_response(
        jsonify({
            'message': 'Collecting game library...'
        }), 202)

    # user not found
    RESP_USER_NOT_FOUND = make_response(
        jsonify({
            'error': 'User not found'
        }), 404)

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
            return render_template(
                'index.jinja2',
                steam_id=steam_id,
                username=user_info.username,
                time_created=user_info.time_created,
                avatar=user_info.avatar)

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
        user_library = buildLibraryForUser(steam_id)
        user_library_value = getLibraryValue(user_library)

        return render_template(
            'profile.jinja2',
            steam_id=steam_id,
            username=user_info.username,
            time_created=user_info.time_created,
            avatar=user_info.avatar,
            game_library=user_library,
            library_value=user_library_value)


# Profile Page (for specific user)
@app.route('/profile/<steam_id>')
def profileById(steam_id):
    if steam_id not in user_info_store:
        user_info_store[steam_id] = User(steam_id)

    user_info = user_info_store[steam_id]
    user_library = buildLibraryForUser(steam_id)
    user_library_value = getLibraryValue(user_library)

    return render_template(
        'profile.jinja2',
        steam_id=steam_id,
        username=user_info.username,
        time_created=user_info.time_created,
        avatar=user_info.avatar,
        game_library=user_library,
        library_value=user_library_value)


# Search results Page
@app.route('/results')
def results():

    # get search params
    keyword = request.args.get('q')
    keyword = keyword.lower()
    results = []

    for (steam_id, user) in user_info_store.items():
        if keyword in user.username:
            results.append({
                'url': '/profile/' + steam_id,
                'text': user.username
            })

    # search games db w/ keyword
    games_results = list(_GAMES.find({'$text': {'$search': keyword}}))
    for game in games_results:
        results.append({
            'url':
            'https://store.steampowered.com/app/{}'.format(game['app_id']),
            'text':
            game['title']
        })

    # serve results
    # print('search results:', results)
    return render_template('results.jinja2', results=results)


# Friends Page
@app.route('/friends')
def friends():
    return render_template('friends.jinja2')


# Get user data by steam_id
@app.route('/user/<steam_id>')
def GetUserInfo(steam_id):

    if steam_id in user_info_store:
        return make_response(jsonify(dict(user_info_store[steam_id])), 200)
    else:
        return RESP_USER_NOT_FOUND


# Get # of games in user's library
#   (specifically: total games vs. loaded games.
#   This endpoint is used to poll load progress)
@app.route('/user/<steam_id>/count')
def GetUserGameCount(steam_id):
    if steam_id in user_info_store:
        result = {
            'total': user_info_store[steam_id].gamecount,
            'loaded': len(user_info_store[steam_id].library)
        }
        if result['total'] > result['loaded']:
            return make_response(jsonify(result), 202)

        else:
            return make_response(jsonify(result), 200)

    else:
        return RESP_USER_NOT_FOUND


# Get user library directly
@app.route('/user/<steam_id>/games')
def GetUserGameLibrary(steam_id):
    if steam_id in user_info_store:
        library = buildLibraryForUser(steam_id)
        return make_response(jsonify(library), 200)
    else:
        return RESP_USER_NOT_FOUND


# Get game details
@app.route('/game/<app_id>')
def GetGame(app_id):
    result = GetGameInfo(app_id)
    if result is not None:
        return make_response(jsonify(dict(result)), 200)


### HELPER functions below
# ------------------------


# Return array of games in user's library in the model {app_id:string, played_time:string, game_data:dict}
def buildLibraryForUser(steam_id):
    if steam_id in user_info_store:

        results = []

        # get list of all user's game ids
        full_app_list = []
        for app in user_info_store[steam_id].library:
            full_app_list.append(app['app_id'])

        # get app data from DB
        db_app_list = []
        db_apps = _GAMES.find({'app_id': {'$in': full_app_list}})
        for app in db_apps:
            # save app_id's to a separte list
            db_app_list.append(app['app_id'])

            # find app play time from user profile
            for lib_app in user_info_store[steam_id].library:
                if app['app_id'] == lib_app['app_id']:
                    played_time = lib_app['played_time']
                    #break

            # format game data
            game_obj = Game(app['app_id'], fetch_data=False)
            game_obj.set_data(
                title=app['title'],
                price=app['price'],
                genre=app['genre'],
                description=app['description'],
                image=app['image'],
                release_date=app['release_date'])

            # gather results per app
            results.append({
                'app_id': app['app_id'],
                'played_time': played_time,
                'game_data': dict(game_obj)
            })

        print('{} apps loaded from DB'.format(len(db_app_list)))

        # calculate # of apps missing in the DB
        missing_app_list = [
            app for app in full_app_list if app not in db_app_list
        ]

        thread = Thread(
            target=LoadMissingGames, args=[missing_app_list, steam_id])
        thread.start()

        return results

# Calculate the total $ value of all games in a library
def getLibraryValue(game_library):
    total_value = decimal.Decimal(0.0)
    for game in game_library:
        price = decimal.Decimal(game['game_data']['price'])
        total_value += price

    return total_value


# fetch Steam data for missing apps and add to DB
def LoadMissingGames(missing_apps, steam_id):
    print('Data missing for {} apps, fetching...'.format(len(missing_apps)))
    for app_id in missing_apps:
        GetGameInfo(app_id)


# Check game data against DB by app_id, add if missing
def GetGameInfo(app_id):
    game_obj = Game(app_id)

    search_game = _GAMES.find_one({'app_id': app_id})
    if search_game is None:
        print('DB has no record for App#{}, fetching data...'.format(app_id))
        game_obj.fetch_data()

        # skip sending to DB if data hasn't loaded
        if game_obj.title == '':
            print('  Fetch failed, skipping...\n')
            return None

        db_result = _GAMES.insert_one(dict(game_obj))
        print('  Added App#{} to the DB: {}\n'.format(app_id,
                                                      db_result.inserted_id))
    else:
        game_obj.set_data(
            title=search_game['title'],
            price=search_game['price'],
            genre=search_game['genre'],
            description=search_game['description'],
            image=search_game['image'],
            release_date=search_game['release_date'])

    return game_obj


# Run the thing
if __name__ == '__main__':
    app.run()
