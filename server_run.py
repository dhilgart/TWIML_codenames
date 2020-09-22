"""
server_run.py: runs the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

import TWIML_codenames
import TWIML_codenames_API_Server
from fastapi import FastAPI
from pydantic import BaseModel

class generate_clues_body(BaseModel):
    clue_word: str
    clue_count: int

class generate_guesses_body(BaseModel):
    guesses: list

root="/"
clientlist=TWIML_codenames_API_Server.clientlist()
gamelist=TWIML_codenames_API_Server.gamelist()

app = FastAPI()

@app.get(root)
def get_player_status(player_id: int, player_key: int):
    if TWIML_codenames_API_Server.validate(player_id,player_key):
        clientlist.client_touch(player_id)
        if clientlist.b_games_to_start:
            gamelist.new_game(clientlist.available_clients)
        return clientlist[player_id].return_status(gamelist)
    else:
        return

@app.get(root+"{game_id}/generate_clue/")
def send_generate_clue_info(game_id: int, player_id: int, player_key: int):
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        clientlist.client_touch(player_id)
        if TWIML_codenames.is_players_turn(gamelist[game_id], player_id):
            team_num, gameboard = gamelist[game_id].solicit_clue_inputs()
            to_return = {'game_id' : game_id,
                         'team_num' : team_num,
                         'gameboard' : gameboard
                         }
            return TWIML_codenames_API_Server.send_as_bytes(to_return)
    else:

    return

@app.post(root+"{game_id}/generate_clue/")
def receive_generate_clue_info(game_id: int, player_id: int, player_key: int, data: generate_clues_body):
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        clientlist.client_touch(player_id)
        if TWIML_codenames.is_players_turn(gamelist[game_id], player_id):
            clue_word = data.clue_word
            clue_count = data.clue_count
            gamelist[game_id].clue_given(clue_word, clue_count)
    else:

    return

@app.get(root+"{game_id}/generate_guesses/")
def send_generate_guesses_info(game_id: int, player_id: int, player_key: int):
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        clientlist.client_touch(player_id)
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

    return

@app.post(root+"{game_id}/generate_guesses/")
def receive_generate_guesses_info(game_id: int, player_id: int, player_key: int, data: generate_guesses_body):
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        clientlist.client_touch(player_id)
        if TWIML_codenames.is_players_turn(gamelist[game_id], player_id):
            guesses = data.guesses
            gamelist[game_id].guesses_given(guesses)
    else:

    return

