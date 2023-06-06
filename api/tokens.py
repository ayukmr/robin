from os import path
import json

def get_token(token):
    """Get token for API call"""

    dir_path = path.dirname(__file__)

    # get tokens from file
    with open(f'{dir_path}/../tokens.json') as file:
        data = json.load(file)

    return data[token]
