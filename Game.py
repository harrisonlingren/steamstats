import requests, os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STEAM_API_URL = 'https://api.steampowered.com/'
print(STEAM_API_KEY)
def GetLibrary(steam_id):
    UserLibraryReqStr = STEAM_API_URL + 'IPlayerService/GetOwnedGames' \
        + '/v1/?key=' + STEAM_API_KEY + '&steamids=' + steam_id \
        + '&include_free_games=1&format=json'

    UserLibraryReq = requests.get(UserLibraryReqStr)
    UserLibrary = UserLibraryReq.json()
    return UserLibrary

#def GetGameInfo(game_id):
