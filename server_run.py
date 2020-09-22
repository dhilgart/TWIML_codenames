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
        return clientlist[player_id].return_status
    else:
        return

@app.get(root+"{game_id}/generate_clue/")
def send_generate_clue_info(game_id: int, player_id: int, player_key: int):
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        clientlist.client_touch(player_id)
        if TWIML_codenames.is_players_turn(gamelist[game_id], player_id):
            
    else:

    return

@app.post(root+"{game_id}/generate_clue/")
def receive_generate_clue_info(game_id: int, player_id: int, player_key: int, data: generate_clues_body):
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        clientlist.client_touch(player_id)
        clue_word = data.clue_word
        clue_count = data.clue_count
    else:

    return

@app.get(root+"{game_id}/generate_guesses/")
def send_generate_guesses_info(game_id: int, player_id: int, player_key: int):
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        clientlist.client_touch(player_id)
    else:

    return

@app.post(root+"{game_id}/generate_guesses/")
def receive_generate_guesses_info(game_id: int, player_id: int, player_key: int, data: generate_guesses_body):
    if TWIML_codenames_API_Server.validate(player_id, player_key):
        clientlist.client_touch(player_id)
        guesses = data.guesses
    else:

    return

