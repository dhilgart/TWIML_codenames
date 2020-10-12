"""
TWIML_codenames_API_Client.py: Module containing functions to interact with the server for TWIMLfest 2020 codenames
    competition
Dan Hilgart <dhilgart@gmail.com>

notes:
    if you change the name of my_model.py, make sure to update it in the imports section

Contains 4 functions:
    check_status(player_id, player_key) [dict] : Asks the server what the current status is for this contestant. Returns
        the status_dict for the player (as defined in the docstring for this function below)
    query_and_respond(player_id, player_key, game_id, role) : Asks the server for the necessary inputs, calls the
        appropriate function from my_model.py, and sends the outputs from that function back to the server
    check_if_new_game(active_games, game_id) : Checks whether this is the first time the local user has seen this
        game_id. If so, prints a notification and adds it to active_games
    check_for_ended_games(local_active_games, status_active_games, player_id, player_key) :

Contains the following global variables (set at the bottom of this file):
    root_url [str] : the url of the server
"""

"""
------------------------------------------------------------------------------------------------------------------------
                                                         To Do
------------------------------------------------------------------------------------------------------------------------
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
from datetime import datetime, timedelta
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

    @param player_id (int): the contestant's player_id
    @param player_key (int): the contestant's player_key
    @param game_id (int): the unique 6-digit identifier for this game
    @param role(str): 'spymaster' or 'operative'
    """
    if role == 'spymaster':
        # add error handling below
        r = requests.get(url=f'{root_url}/{game_id}/generate_clue/',
                         params={'player_id': player_id, 'player_key': player_key})
        returned = pickle.loads(r.content)
        team_num = returned['team_num']
        gameboard = returned['gameboard']
        print(f'{datetime.now()}: game {game_id} generate_clue inputs received (team={team_num})')

        start_time=datetime.now()
        clue_word, clue_count = model.generate_clue(game_id, team_num, gameboard)
        print(f'{datetime.now()}: game {game_id} clue generated. Elapsed time = {datetime.now() - start_time}')

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
        print(f'{datetime.now()}: game {game_id} generate_guesses inputs received (team={team_num})')

        start_time = datetime.now()
        guesses = model.generate_guesses(game_id, team_num, clue_word, clue_count, unguessed_words, boardwords,
                                         boardmarkers)
        print(f'{datetime.now()}: game {game_id} guesses generated. Elapsed time = {datetime.now() - start_time}')

        requests.post(url=f'{root_url}/{game_id}/generate_guesses/',
                      params={'player_id': player_id, 'player_key': player_key},
                      json={'guesses': guesses})

async def check_if_new_game(active_games, game_id):
    """
    Checks whether this is the first time the local user has seen this game_id. If so, prints a notification and adds it
        to active_games

    @param active_games [list[int]] : the list of game_ids the local user thinks are active
    @param game_id [int] : the unique 6-digit identifier for this game

    @returns active_games [list[int]] : the updated active_games list
    """
    if game_id not in active_games:
        print(f'{datetime.now()}: game {game_id} started')
        active_games.append(game_id)
    return active_games

async def check_for_ended_games(local_active_games, status_active_games, player_id, player_key):
    """
    Checks whether any games in local_active_games are no longer in status_active_games. If so, pulls the game log for
        that game so that the reason for ending can be printed. Updates local_active_games as necessary

    @param local_active_games [list[int]] : the list of game_ids the local user thinks are active
    @param status_active_games [list[int]] : the list of game_ids that actually are active
    @param player_id [int] : the contestant's player_id
    @param player_key [int] : the contestant's player_key

    @returns local_active_games [list[int]] : the updated local_active_games list
    """
    for game_id in local_active_games:
        if game_id not in status_active_games:
            local_active_games.remove(game_id)
            r = requests.get(url=f'{root_url}/{game_id}/log/',
                             params={'player_id': player_id, 'player_key': player_key})
            returned = pickle.loads(r.content)
            game_log = returned
            if game_log['events'][-1]['event'] == 'game over':
                # game completed successfully
                end_reason = game_log['events'][-1]['reason']
                winning_team_ids = [player['player_id'] for player in game_log['winning team']['players']]
                if player_id in winning_team_ids:
                    print(f'{datetime.now()}: game {game_id} ended: {end_reason}. Result = win!')
                else:
                    print(f'{datetime.now()}: game {game_id} ended: {end_reason}. Result = loss')
            else:
                # game timed out; did not complete
                timedout_player_id = game_log['timed out waiting on']['player_id']
                if timedout_player_id == player_id:
                    print(f'{datetime.now()}: game {game_id} ended: timed out waiting on you!')
                else:
                    print(f'{datetime.now()}: game {game_id} ended: timed out waiting on {timedout_player_id}')
    return local_active_games

"""
------------------------------------------------------------------------------------------------------------------------
                                                    Global Variables
------------------------------------------------------------------------------------------------------------------------
"""
root_url = 'http://twiml-codenames.herokuapp.com'