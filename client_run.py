"""
client_run.py: run this file to participate in the TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

import TWIML_codenames
import TWIML_codenames_API_Client
import my_model as model
import asyncio
import json

async def check_status_loop():
    """
    The main loop that creates a new task every X seconds to find out whether anything is expected from the player
    """
    while True:
        loop.create_task(check_status())
        await asyncio.sleep(60)

async def check_status():
    """
    Asks the server what the current status is for this player.
    """
    await status = TWIML_codenames_API_Client.check_status(loop, user_id, user_key)


if __name__ == "__main__":
    UserID_Key = json.load(open('myUserID-Key.txt', 'r'))
    user_id = UserID_Key.user_id
    user_key = UserID_Key.user_key

    loop = asyncio.get_event_loop()
    task = loop.create_task(check_status_loop())

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
