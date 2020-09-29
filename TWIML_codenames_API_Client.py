"""
TWIML_codenames_API_Client.py: Module containing functions to interact with the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

import my_model as model
import TWIML_codenames
import requests
import pickle

root_url = 'http://twiml-codenames.herokuapp.com'

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
    r = requests.get(url=root_url+'/', params={'player_id': player_id, 'player_key': player_key})
    status_dict = pickle.loads(r.content)
    return status_dict

async def query_and_respond(player_id, player_key, game_id, role):
    """

    """
    if role == 'spymaster':
        # add error handling below
        r = requests.get(url=f'{root_url}/{game_id}/generate_clue/',
                         params={'player_id': player_id, 'player_key': player_key})
        returned = pickle.loads(r.content)
        team_num = returned['team_num']
        gameboard = returned['gameboard']
        clue_word, clue_count = model.generate_clue(game_id, team_num, gameboard)
        requests.post(url=f'{root_url}/{game_id}/generate_clue/',
                      params={'player_id': player_id, 'player_key': player_key},
                      json={'clue_word':clue_word, 'clue_count':clue_count})

    elif role == 'operative':
        # add error handling below
        r = requests.get(url=f'{root_url}/{game_id}/generate_guesses/',
                         params={'player_id': player_id, 'player_key': player_key})
        returned = pickle.loads(r.content)
        team_num = returned['team_num']
        clue_word = returned['clue_word']
        clue_count = returned['clue_count']
        unguessed_words = returned['unguessed_words']
        boardwords = returned['boardwords']
        boardmarkers = returned['boardmarkers']
        guesses = model.generate_guesses(game_id, team_num, clue_word, clue_count, unguessed_words, boardwords,
                                         boardmarkers)
        requests.post(url=f'{root_url}/{game_id}/generate_guesses/',
                      params={'player_id': player_id, 'player_key': player_key},
                      json={'guesses': guesses})