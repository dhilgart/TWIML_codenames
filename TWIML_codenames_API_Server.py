"""
TWIML_codenames_API_Server.py: Module to run the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

from fastapi import FastAPI, Response
import pickle

app = FastAPI()

@app.get("/")
def send_as_bytes():
    var_to_send=''
    return Response(content=pickle.dumps(var_to_send))
