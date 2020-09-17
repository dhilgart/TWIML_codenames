"""
TWIML_codenames_API_Server.py: Module to run the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

from fastapi import FastAPI, Response
from pydantic import BaseModel
import pickle

class generate_clues_body(BaseModel):
    clue_word: str
    clue_count: int

class generate_guesses_body(BaseModel):
    guesses: list

root="/"
app = FastAPI()

def send_as_bytes(var_to_send):
    return Response(content=pickle.dumps(var_to_send))

@app.get(root+"{game_id}/generate_clue")
def send_generate_clue_info(game_id: int, user_id: int, user_key: int):
    return

@app.post(root+"{game_id}/generate_clue")
def receive_generate_clue_info(game_id: int, user_id: int, user_key: int, data: generate_clues_body):
    clue_word=data.clue_word
    clue_count=data.clue_count
    return

@app.get(root+"{game_id}/generate_guesses")
def send_generate_guesses_info(game_id: int, user_id: int, user_key: int):
    return

@app.post(root+"{game_id}/generate_guesses")
def receive_generate_guesses_info(game_id: int, user_id: int, user_key: int, data: generate_guesses_body):
    guesses = data.guesses
    return

