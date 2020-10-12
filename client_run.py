"""
client_run.py: run this file (using "python client_run.py") to participate in the TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>

This file starts an async event loop and then adds a new task each X seconds to ping the server and get the current
    status for the player. If the server is waiting for this player, it will call
    TWIML_codenames_API_Client.query_and_respond() which in turn:
        asks the server for the necessary inputs
        calls the appropriate function from my_model.py
        sends the outputs from that function back to the server
"""

import TWIML_codenames_API_Client
import asyncio
import json

async def check_status_loop(active_games):
    """
    The main loop that creates a new task every X seconds to find out whether anything is expected from the player
    """
    while True:
        loop.create_task(check_status(active_games))
        await asyncio.sleep(1)

async def check_status(active_games):
    """
    Asks the server what the current status is for this player. If the server is waiting for a query from the player,
        adds a task to the loop to query and respond which then:
            asks the server for the necessary inputs
            calls the appropriate function from my_model.py
            sends the outputs from that function back to the server
    """
    # request the status from the server:
    status = await TWIML_codenames_API_Client.check_status(player_id, player_key)

    # Have any active games ended?
    active_games = await TWIML_codenames_API_Client.check_for_ended_games(active_games, status['active games'].keys(),
                                                                          player_id, player_key)

    # Does the player have any active games?
    if len(status['active games']) > 0:
        # For each active game...
        for game_data in status['active games'].values():
            # is this a new game?
            active_games = await TWIML_codenames_API_Client.check_if_new_game(active_games, game_data['game_id'])

            # ...check if the server is waiting on this player:
            if game_data['waiting on']['player_id'] == player_id:
                # if so, call query_and_respond()
                loop.create_task(TWIML_codenames_API_Client.query_and_respond(player_id=player_id,
                                                                              player_key=player_key,
                                                                              game_id=game_data['game_id'],
                                                                              role=game_data['waiting on']['role']
                                                                              ))

if __name__ == "__main__":
    # Load player_id and player_key from the myPlayerID-Key.txt file
    PlayerID_Key = json.load(open('myPlayerID-Key.txt', 'r'))
    player_id = int(PlayerID_Key['Player_ID'])
    player_key = int(PlayerID_Key['Player_Key'])

    active_games = []

    # Create the async event loop
    loop = asyncio.get_event_loop()
    task = loop.create_task(check_status_loop(active_games))

    # run the loop
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
