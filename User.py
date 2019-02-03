import requests, os, json
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from Game import Game

load_dotenv(find_dotenv())

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_API_URL = 'https://api.steampowered.com/'


class User:
    # class attributes
    username = ''
    avatar = ''
    steam_id = ''
    time_created = ''
    library = {}
    gamecount = 0

    # intialize class
    def __init__(self, steam_id):
        request_uri = STEAM_API_URL + 'ISteamUser/GetPlayerSummaries' \
            + '/v1?key=' + STEAM_API_KEY + '&steamids=' + steam_id \
            + '&format=json'
        r = requests.get(request_uri)
        user_info = r.json()['response']['players']['player'][0]
        self.username = user_info['personaname']
        self.avatar = user_info['avatarfull']
        self.steam_id = steam_id
        self.time_created = datetime.fromtimestamp(user_info['timecreated'])
        self.library = {}

    # Fetches the user's game library
    def GetLibrary(self):
        request_uri = STEAM_API_URL + 'IPlayerService/GetOwnedGames' \
            + '/v1?key=' + STEAM_API_KEY + '&steamid=' + self.steam_id \
            + '&include_played_free_games=1&format=json'

        library_req = requests.get(request_uri)
        library_array = library_req.json()['response']['games']

        self.gamecount = len(library_array)

        for game in library_array:
            steam_id = str(game['appid'])
            self.library[steam_id] = {
                'game': Game(steam_id),
                'played_time': game['playtime_forever']
            }

        return self.library

    def asdict(self):
        d = {}

        d['username'] = self.username
        d['avatar'] = self.avatar
        d['steam_id'] = self.steam_id
        d['time_created'] = self.time_created

        d['library'] = {}
        for app_id, gamevals in self.library.items():
            d['library'][app_id] = {
                'game': dict(gamevals['game']),
                'played_time': gamevals['played_time']
            }

        return d

    def __str__(self):
        return str(self.asdict())