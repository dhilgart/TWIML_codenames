"""
TWIML_codenames_API_Server.py: Module to run the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

from fastapi import FastAPI, Response
import pickle

root="/"
app = FastAPI()

def send_as_bytes(var_to_send):
    return Response(content=pickle.dumps(var_to_send))

@app.get(root+"generate_clue/")
def send_generate_clue_info():
    return

@app.post(root+"generate_clue/")
def receive_generate_clue_info():
    return

@app.get(root+"generate_guesses/")
def send_generate_guesses_info():
    return

@app.post(root+"generate_guesses/")
def receive_generate_guesses_info():
    return

