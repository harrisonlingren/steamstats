import requests, os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STEAM_API_URL = 'https://api.steampowered.com/'

class Game:
    # class attributes
    app_id = ''

    def __init__(self, app_id):
        self.app_id = app_id