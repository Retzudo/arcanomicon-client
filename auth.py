import logging

import requests

import settings


def login_prompt():
    """Prompt the user to input their credentials."""
    username = input('Username: ')
    passwword = input('Password: ')

    return username, passwword


def log_in(username, password):
    """Log in with username and password and return the JWT."""
    response = requests.post(settings.URLS['auth'], {
        'username': username,
        'password': password,
    })

    if response.status_code == 200:
        return response.json().get('token')
    else:
        raise RuntimeError('Could not authenticate.', response)


def read_token():
    """Read the token from the token file and return it."""
    with open(settings.FILES['token']) as f:
        return f.read().strip()


def write_token(token):
    """Write the token to the token file."""
    with open(settings.FILES['token'], 'w') as f:
        return f.write(token)


def get_token():
    token = read_token()
    logging.debug('Token read from file:', token)

    if not token:
        logging.debug('Token could not be read from file.')
        token = log_in(*login_prompt())
        logging.debug('Writing token token to file.')
        write_token(token)

    return token
