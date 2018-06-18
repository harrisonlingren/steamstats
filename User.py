import requests, os, json
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
        self.time_created = user_info['timecreated']
        self.library = self.__GetLibrary()
    
    # Fetches the user's game library
    def __GetLibrary(self):
        request_uri = STEAM_API_URL + 'IPlayerService/GetOwnedGames' \
            + '/v1?key=' + STEAM_API_KEY + '&steamid=' + self.steam_id \
            + '&include_played_free_games=1&format=json'

        library_req = requests.get(request_uri)
        library_array = library_req.json()['response']['games']

        library = {}
        for game in library_array:
            steamid = str(game['appid'])
            library[steamid] = Game(steamid)
        
        print(library)

        return library