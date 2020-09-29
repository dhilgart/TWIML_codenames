"""
client_run.py: run this file to participate in the TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

import TWIML_codenames_API_Client
import asyncio
import json

async def check_status_loop():
    """
    The main loop that creates a new task every X seconds to find out whether anything is expected from the player
    """
    while True:
        loop.create_task(check_status())
        await asyncio.sleep(5)

async def check_status():
    """
    Asks the server what the current status is for this player and if the server is waiting for a query from the player,
    adds a task to the loop to query and respond
    """
    status = await TWIML_codenames_API_Client.check_status(player_id, player_key)
    if len(status['active games']) > 0:
        for game_data in status['active games'].values():
            if game_data['waiting on']['player_id'] == player_id and game_data['waiting on']['waiting for'] == 'query':
                loop.create_task(TWIML_codenames_API_Client.query_and_respond(player_id=player_id,
                                                                              player_key=player_key,
                                                                              game_id=game_data['game_id'],
                                                                              role=game_data['waiting on']['role']
                                                                              ))

if __name__ == "__main__":
    PlayerID_Key = json.load(open('myPlayerID-Key.txt', 'r'))
    player_id = int(PlayerID_Key['Player_ID'])
    player_key = int(PlayerID_Key['Player_Key'])

    loop = asyncio.get_event_loop()
    task = loop.create_task(check_status_loop())

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
