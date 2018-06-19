import requests, os
from datetime import datetime
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

        if game_info_request.json()[app_id]['success']:
            game_info = game_info_request.json()[app_id]['data']

            self.id = app_id
            self.title = game_info['name']
            
            if game_info['is_free'] == True:
                self.price = '0.00'
            elif game_info['is_free'] == False:

                # format price string from cents
                try:
                    self.price = str(game_info['price_overview']['final'])[:-2] \
                        + '.' + str(game_info['price_overview']['final'])[-2:]
                except KeyError:
                    self.price = '0.00'
            
            # concat genres
            try:
                if len(game_info['genres']) > 1:
                    self.genre = game_info['genres'][0]['description']
                    for genre in game_info['genres'][1:]:
                        self.genre += ', ' + genre['description']
                else:
                    self.genre = game_info['genres'][0]['description']
            except KeyError:
                self.genre = ''
            
            self.description = game_info['detailed_description']
            self.image = game_info['header_image']
            self.release_date = game_info['release_date']['date']

    def __iter__(self):
        yield 'app_id', self.app_id
        yield 'title', self.title
        yield 'price', self.price
        yield 'description', self.description
        yield 'image', self.image
        yield 'release_date', self.release_date
        yield 'genre', self.genre

    def __str__(self):
        return str(dict(self))