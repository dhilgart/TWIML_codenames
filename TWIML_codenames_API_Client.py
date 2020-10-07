"""
TWIML_codenames_API_Client.py: Module containing functions to interact with the server for TWIMLfest 2020 codenames
    competition
Dan Hilgart <dhilgart@gmail.com>

notes:
    if you change the name of my_model.py, make sure to update it in the imports section

Contains 2 functions:
    check_status(player_id, player_key) [dict] : Asks the server what the current status is for this contestant. Returns
        the status_dict for the player (as defined in the docstring for this function below)
    query_and_respond(player_id, player_key, game_id, role) :

Contains the following global variables (set at the bottom of this file):
    root_url [str] : the url of the server
"""

"""
------------------------------------------------------------------------------------------------------------------------
                                                         To Do
------------------------------------------------------------------------------------------------------------------------
    - Add print statements to let the competitor know when games start and end
    - Add error handling throughout
"""

"""
------------------------------------------------------------------------------------------------------------------------
                                                        Imports
------------------------------------------------------------------------------------------------------------------------
"""
import my_model as model # if you change the name of my_model.py, update it here
import TWIML_codenames # needed because query_and_respond sometimes handles TWIML_codenames.Gameboard objects
import requests
import pickle
"""
------------------------------------------------------------------------------------------------------------------------
                                                       Functions
------------------------------------------------------------------------------------------------------------------------
"""
async def check_status(player_id, player_key):
    """
    Asks the server what the current status is for this contestant.
    @param player_id (int): the contestant's player_id
    @param player_key (int): the contestant's player_key
    @returns status_dict (dict): a nested dictionary of form {'active games' : game_statuses,
        'ended games' : list[game_ids]}. game_statuses is itself a nested dictionary of form {game_id : game_status}
        with game_status a dictionary of form:
            {'game_id'          : game_id,
             'game_start_time'  : <datetime>,
             'role_info'        : <see role_info as defined in .active_games>,
             'waiting on'       : { 'team'              : <1 or 2>,
                                    'role'              : <'spymaster' or 'operative'>,
                                    'player_id'         : player_id of the player being waited on,
                                    'waiting for'       : <'query' or 'input'>,
                                    'waiting duration'  : <timedelta>
                                  }
            }
    """
    #add error handling below
    r = requests.get(url=root_url+'/', params={'player_id': player_id, 'player_key': player_key})
    status_dict = pickle.loads(r.content)
    return status_dict

async def query_and_respond(player_id, player_key, game_id, role):
    """
    Asks the server for the necessary inputs, calls the appropriate function from my_model.py, and sends the outputs
        from that function back to the server
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
"""
------------------------------------------------------------------------------------------------------------------------
                                                    Global Variables
------------------------------------------------------------------------------------------------------------------------
"""
root_url = 'http://twiml-codenames.herokuapp.com'