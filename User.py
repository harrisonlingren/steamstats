import requests, os, dotenv, json

dotenv.load_dotenv(dotenv.find_dotenv())

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

class User:

    username = ''
    avatar = ''
    steam_id = ''
    time_created = ''

    def __init__(self, steam_id):
        request_uri = 'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v1?key=' + STEAM_API_KEY + '&steamids=' + steam_id
        r = requests.get(request_uri)
        user_info = r.json()['response']['players']['player'][0]
        self.username = user_info['personaname']
        self.avatar = user_info['avatarfull']
        self.steam_id = steam_id
        self.time_created = user_info['timecreated']


