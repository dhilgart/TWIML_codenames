"""
server_run.py: runs the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>

notes:
    This file is written to be run on uvicorn using the FastAPI library by calling 'uvicorn server_run:app' from the
        command line
    This server has 5 functions by which clients can interact with it:
        get(root) : returns the current status for the player
        get(generate_clue) : returns the inputs the player will need to generate a clue
        post(generate_clue) : receives the clue_word and clue_count from the player and updates the game accordingly
        get(generate_guesses) : returns the inputs the player will need to generate a list of guesses
        post(generate_guesses) : receives the list of guesses from the player and updates the game accordingly
    Most of the supporting functions and classes are defined in TWIML_codenames_API_Server
    The first thing done for every request is to validate the player_id with the player_key using
        TWIML_codenames_API_Server.validate(player_id,player_key)
    All returns are sent as bytes (using TWIML_codenames_API_Server.send_as_bytes) so objects (e.g. numpy arrays or
        custom class obejcts) can be encoded
"""

import TWIML_codenames
import TWIML_codenames_API_Server
from fastapi import FastAPI
# pydantic.BaseModel is used to define the expected variable types for the body of the post requests such that they are
# properly recognized as the body:
from pydantic import BaseModel
import uvicorn
import os

class generate_clues_body(BaseModel):
    """
    Defines the expected variable types for the body of the post(generate_clue) request
    """
    clue_word: str
    clue_count: int

class generate_guesses_body(BaseModel):
    """
    Defines the expected variable types for the body of the post(generate_guesses) request
    """
    guesses: list

root="/"

#When starting the server, create the clientlist and gamelist objects for keeping track of the clients and the games
clientlist=TWIML_codenames_API_Server.Clientlist()
gamelist=TWIML_codenames_API_Server.Gamelist(clientlist)

app = FastAPI() # called by uvicorn server_run:app

@app.get(root)
def get_player_status(player_id: int, player_key: int):
    """
    @params player_id, player_key : used for validating player identity

    @returns (bytes): the current status for the player containing info about active and ended games:
        info for active games includes:
            game_id, game start time, role_info (player's team number, player's role, and player's teammate ID),
            info about who the game is waiting on: the player_id of the player whose turn it is, their role, how long
                the game has been waiting for them, and whether the game is waiting for them to query the server or
                provide their inputs to the next phase of the game
        info for ended games includes:
            game_id, role_info (player's team number, player's role, and player's teammate ID), game start time, game
                end time, whether the game completed or timed out, the final gameboard state, and
                    for completed games: the player_id's and Elo impacts for both the winning and losing team
                    for timed out games: the info of who the game was waiting on when it timed out
    """
    if TWIML_codenames_API_Server.validate(player_id,player_key):
        # any time a client interacts with the server, record the touch (updating the last_active time for this client)
        clientlist.client_touch(player_id)

        # If this is a new client checking in for the first time, the client_touch action could put the
        #   available_clients over the threshold for starting a new game. Therefore, check if a game can be started:
        if clientlist.b_games_to_start:
            gamelist.new_game(clientlist.available_clients)

        # regardless if a new game has started or not, call the following function to determine what status to return
        to_return = clientlist[player_id].return_status(gamelist)
        return TWIML_codenames_API_Server.send_as_bytes(to_return)
    else:
        return 'Will not get here: no validation configured yet'

@app.get(root+"{game_id}/generate_clue/")
def send_generate_clue_info(game_id: int, player_id: int, player_key: int):
    """
    @param game_id (int) : the ID of the game being queried
    @params player_id, player_key : used for validating player identity

    @returns (bytes):
        If it is the player's turn to take this action:
            game_id (int)
            team_num (int) : the team number of the current player (1 or 2)
            gameboard (TWIML_codenames.Gameboard object) : the current state of the gameboard. Includes:
                the 5x5 grid of words for the current game (gameboard.boardwords),
                the key for which words belong to which team (gameboard.boardkey),
                and a boardmarkers array that tracks which words have been guessed so far (gameboard.boardmarkers)
        Otherwise, returns the current status for this player
    """
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        # any time a client interacts with the server, record the touch (updating the last_active time for this client)
        clientlist.client_touch(player_id)
        if gamelist.is_active_game(game_id):
            if TWIML_codenames.is_players_turn(gamelist[game_id], player_id):
                team_num, gameboard = gamelist[game_id].solicit_clue_inputs()
                to_return = {'game_id' : game_id,
                             'team_num' : team_num,
                             'gameboard' : gameboard
                             }
                return TWIML_codenames_API_Server.send_as_bytes(to_return)
            else:
                to_return = clientlist[player_id].return_status(gamelist)
                return TWIML_codenames_API_Server.send_as_bytes(to_return)
        else:
            to_return = clientlist[player_id].return_status(gamelist)
            return TWIML_codenames_API_Server.send_as_bytes(to_return)
    else:
        return 'Will not get here: no validation configured yet'

@app.post(root+"{game_id}/generate_clue/")
def receive_generate_clue_info(game_id: int, player_id: int, player_key: int, data: generate_clues_body):
    """
    receives the clue_word and clue_count from the player and calls the clue_given function from the
        TWIML_codenames.Game object

    @param game_id (int) : the ID of the game being queried
    @params player_id, player_key : used for validating player identity
    @param data (generate_clues_body object) : This object contains
        clue_word (str) : the clue word to be given to the player's partner
        clue_count (int) : the number of words which the player thinks are related to the clue word

    @returns (bytes): the current status for this player
    """
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        # any time a client interacts with the server, record the touch (updating the last_active time for this client)
        clientlist.client_touch(player_id)
        if gamelist.is_active_game(game_id):
            if TWIML_codenames.is_players_turn(gamelist[game_id], player_id):
                clue_word = data.clue_word
                clue_count = data.clue_count
                gamelist[game_id].clue_given(clue_word, clue_count)
            to_return = clientlist[player_id].return_status(gamelist)
            return TWIML_codenames_API_Server.send_as_bytes(to_return)
        else:
            to_return = clientlist[player_id].return_status(gamelist)
            return TWIML_codenames_API_Server.send_as_bytes(to_return)
    else:
        return 'Will not get here: no validation configured yet'

@app.get(root+"{game_id}/generate_guesses/")
def send_generate_guesses_info(game_id: int, player_id: int, player_key: int):
    """
    @param game_id (int) : the ID of the game being queried
    @params player_id, player_key : used for validating player identity

    @returns (bytes):
        If it is the player's turn to take this action:
            game_id (int)
            team_num (int) : the team number of the current player (1 or 2)
            clue_word (str) : the clue word given by the player's partner
            clue_count (int) : the number of words which are related to the clue word (as given by the player's partner)
            unguessed_words (list[str]) : a list of all the words that have not yet been guessed
            boardwords (np.array) : the 5x5 grid of words for the current game
            boardmarkers (np.array) : the array that tracks which words have been guessed so far and which team they
                belong to
        Otherwise, returns the current status for this player
    """
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        # any time a client interacts with the server, record the touch (updating the last_active time for this client)
        clientlist.client_touch(player_id)
        if gamelist.is_active_game(game_id):
            if TWIML_codenames.is_players_turn(gamelist[game_id], player_id):
                team_num, clue_word, clue_count, unguessed_words, boardwords, boardmarkers = \
                    gamelist[game_id].solicit_guesses_inputs()
                to_return = {'game_id' : game_id,
                             'team_num' : team_num,
                             'clue_word' : clue_word,
                             'clue_count' : clue_count,
                             'unguessed_words' : unguessed_words,
                             'boardwords' : boardwords,
                             'boardmarkers' : boardmarkers
                             }
                return TWIML_codenames_API_Server.send_as_bytes(to_return)
            else:
                to_return = clientlist[player_id].return_status(gamelist)
                return TWIML_codenames_API_Server.send_as_bytes(to_return)
        else:
            to_return = clientlist[player_id].return_status(gamelist)
            return TWIML_codenames_API_Server.send_as_bytes(to_return)
    else:
        return 'Will not get here: no validation configured yet'

@app.post(root+"{game_id}/generate_guesses/")
def receive_generate_guesses_info(game_id: int, player_id: int, player_key: int, data: generate_guesses_body):
    """
    receives the list of guesses from the player and calls the guesses_given function from the
        TWIML_codenames.Game object

    @param game_id (int) : the ID of the game being queried
    @params player_id, player_key : used for validating player identity
    @param data (generate_guesses_body object) : This object contains
        guesses (list[str]) : a list of the words that the player wants to try guessing (in the order to be tried)

    @returns (bytes): the current status for this player
    """
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        # any time a client interacts with the server, record the touch (updating the last_active time for this client)
        clientlist.client_touch(player_id)
        if gamelist.is_active_game(game_id):
            if TWIML_codenames.is_players_turn(gamelist[game_id], player_id):
                guesses = data.guesses
                gamelist[game_id].guesses_given(guesses)
            to_return = clientlist[player_id].return_status(gamelist)
            return TWIML_codenames_API_Server.send_as_bytes(to_return)
        else:
            to_return = clientlist[player_id].return_status(gamelist)
            return TWIML_codenames_API_Server.send_as_bytes(to_return)
    else:
        return 'Will not get here: no validation configured yet'

if __name__ == "__main__":
   PORT = os.environ.get("PORT",8000)
   uvicorn.run("server_run:app", host="0.0.0.0", port=PORT, log_level="debug"
                )