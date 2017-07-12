import os
import appdirs
from requests.compat import urljoin
import configparser


APP_NAME = 'Arcanomicon'
AUTHOR = 'Retzudo'
CONFIG_DIR = appdirs.user_config_dir(APP_NAME, AUTHOR, roaming=True)
DATA_DIR = appdirs.user_data_dir(APP_NAME, AUTHOR, roaming=True)

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    'settings': os.path.join(CONFIG_DIR, 'settings.ini'),
    'token': os.path.join(CONFIG_DIR, 'token.txt'),
    'database': os.path.join(DATA_DIR, 'database.txt'),
}


def make_files():
    for _, file_name in FILES.items():
        if not os.path.exists(file_name):
            with open(file_name, 'w+'):
                pass

# Ensure the needed file exist
make_files()

parser = configparser.ConfigParser()
parser.read(FILES['settings'])
CONFIG = parser['Arcanomicon']

DEFAULT_BASE_URL = 'https://arcanomicon.com/api/'
BASE_URL = CONFIG.get('BaseUrl', DEFAULT_BASE_URL)
URLS = {
    'auth': urljoin(BASE_URL, 'jwt-auth'),
    'favourites': urljoin(BASE_URL, 'favourites'),
    'add_on_details': urljoin(BASE_URL, 'addons/{id}'),
}