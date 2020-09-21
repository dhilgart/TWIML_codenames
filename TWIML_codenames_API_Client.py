"""
TWIML_codenames_API_Client.py: Module containing functions to interact with the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

import requests

root_url = 'http://127.0.0.1:8000/'

async def check_status(player_id, player_key):
    """
    Asks the server what the current status is for this contestant.
    @param player_id (int): the contestant's player_id
    @param player_key (int): the contestant's player_key
    @returns status_dict (dict): the return status dictionary containting the status and any additional info required.
        Possible return statuses include:
        -   asdf
        -   asdf
    """
    #add error handling below
    await r = requests.get(url=root_url, params={'player_id': player_id, 'player_key': player_key})
    status_dict = r.json()
    return status_dict
