import requests, os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STEAM_API_URL = 'https://api.steampowered.com/'
STEAM_STORE_API_URL = 'https://store.steampowered.com/api/'

class Game:
    # class attributes
    id = ''
    title = ''
    price = ''
    genre = ''
    description = ''
    image = ''
    release_date = ''


    def __init__(self, app_id):
        self.app_id = app_id

        request_uri = STEAM_STORE_API_URL \
            + 'appdetails?appids=' + app_id

        print(request_uri)
        
        game_info_request = requests.get(request_uri)
        game_info = game_info_request.json()[app_id]['data']

        self.id = app_id
        self.title = game_info['name']
        
        # format price string from cents
        self.price = str(game_info['price_overview']['final'])[:-2] \
            + '.' + str(game_info['price_overview']['final'])[-2:]
        
        # concat genres
        if len(game_info['genres']) > 1:
            self.genre = game_info['genres'][0]['description']
            for genre in game_info['genres'][1:]:
                self.genre += ', ' + genre['description']
        else:
            self.genre = game_info['genres'][0]['description']
        
        self.description = game_info['detailed_description']
        self.image = game_info['header_image']
        self.release_date = game_info['release_date']['date']