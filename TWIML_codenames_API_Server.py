"""
TWIML_codenames_API_Server.py: containing functions called by the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>

Contains 4 class definitions:
    Clientlist : Keeps track of which clients are currently actively interacting with the server
    Client : Stores info about an individual client
    Gamelist : Keeps track of which games are currently in progress and stores info for those that have completed
    MongoLogger : Interfaces with MongoDB to write the log for an individual game

Contains 7 functions:
    validate(player_id, player_key) [bool] : returns True if the player_key is the correct one for the player_id
    send_as_bytes(var_to_send) [fastapi.Response] : converts any object (including a dict filled with various objects)
        into bytes to be sent via the API
    get_leaderboards(db) [dict] : pulls the current leaderboards from the players MongoDB
    list_player_games(player_to_pull, db) [list[int]] : returns a list of game_ids for all games this player is/was
        involved in
    list_completed_games(db) [list[int]] : returns a list of game_ids for all completed games
    pull_game_log(game_id, player_id, db) [dict] : returns the game log for an individual game
    scrub_game_log(game_dict, player_id) [dict] : removes info from the game log that would not be known to the
        player_id who is pulling the log

Contains the following global variables (set at the bottom of this file):
    client_active_timeout [timedelta] : how often a client needs to interact with the server to remain active
    min_clients_to_start_new_game [int] : how large the queue of available players needs to be before a new game can be
        started
    max_active_games_per_player [int] : how many games a player can participate in at once
    wordlist list[str] : the list of words from which the gameboards will randomly select 25 words when generated
    player_keys [pandas dataframe] : the list of player_ids and associated player_keys for use in player validation
"""

"""
------------------------------------------------------------------------------------------------------------------------
                                                         To Do
------------------------------------------------------------------------------------------------------------------------
    - Save/load gamelist to/from disk?
"""

"""
------------------------------------------------------------------------------------------------------------------------
                                                        Imports
------------------------------------------------------------------------------------------------------------------------
"""
import TWIML_codenames
import pandas as pd
from datetime import datetime, timedelta
from fastapi import Response # needed for transmitting information in byte format
import pickle
import random
from copy import deepcopy
"""
------------------------------------------------------------------------------------------------------------------------
                                                        Classes
------------------------------------------------------------------------------------------------------------------------
"""
class Clientlist(object):
    """
    Keeps track of which clients are currently actively interacting with the server
    Individual clients can be called externally via Clientlist[player_id]: see __getitem__

    Instance variables:
        .clients [dict] : a dictionary of form {player_id : TWIML_codenames_API_server.Client} for each client who has
            interacted with the server since it was last started.
        .db [pymongo database] : a pointer to the pymongo database connection

    Functions:
        .client_touch(player_id) : Called whenever a client interacts with the server to prevent them timing out
        .add_client(player_id) : Used to add new clients to the clientlist

    Properties:
        .active_clients [list[TWIML_codenames_API_server.Client]] : returns a list of all clients that are currently
            active
        .available_clients [list[TWIML_codenames_API_server.Client]] : returns a list of all clients that are currently
            available to start a new game
        .b_games_to_start [bool] : True if there are enough available clients in .available_clients to start a new game
    """
    def __init__(self, db):
        """
        Instantiate a new Clientlist

        @param db [pymongo database] : a pointer to the pymongo database connection
        """
        self.clients = {}
        self.db = db

    def __getitem__(self, key):
        return self.clients[key]
    
    def client_touch(self, player_id):
        """
        Updates the last_active timestamp for the client
        Called whenever a client sends any get or post to the server
        Checks if the client has been seen before. If this is the client's first interaction with the server, calls
            add_client(player_id)

        @param player_id [int] : the unique 4-digit player identifier
        """
        if player_id in self.clients.keys():
            self.clients[player_id].touch()
        else:
            self.add_client(player_id)

    def add_client(self, player_id):
        """
        Creates a new client object and adds it to the self.clients dict
        The only way a new client is added is if this func is called by client_touch(player_id)

        @param player_id [int] : the unique 4-digit player identifier
        """
        self.clients[player_id] = Client(player_id, self.db)

    @property
    def active_clients(self):
        """
        @returns [list[TWIML_codenames_API_server.Client]] : a list of all the clients that are currently active (those
            who have interacted with the server in any way within the client_active_timeout duration)
        """
        active_clients = [client for client in self.clients.values() if client.active]
        return active_clients

    @property
    def available_clients(self):
        """
        @returns [list[TWIML_codenames_API_server.Client]] : a list of currently active clients who aren't involved in a
            game already
        """
        available_clients = [client for client in self.active_clients
                             if client.num_active_games < max_active_games_per_player]
        return available_clients

    @property
    def b_games_to_start(self):
        """
        Is the number of available clients >= the minimum number of clients to start a new game?

        @returns [bool] : True if a new game can be started
        """
        return len(self.available_clients) >= min_clients_to_start_new_game

class Client(object):
    """
    Stores info about an individual client

    Instance variables:
        .player_id [int] : the unique 4-digit player identifier
        .player [TWIML_codenames.Player] : the TWIML_codenames.Player object for this player
        .last_active [datetime] : the timestamp of the most recent time the client interacted with the server
        .prev_active [datetime] : the timestamp of the 2nd-most recent time the client interacted with the server
        .active_games [dict] : a nested dictionary of form {game_id : role_info} for each active game this player is
            involved in. role_info is itself a dictionary of form:
                {'team'         : <1 or 2>,
                 'role'         : <'spymaster' or 'operative'>,
                 'teammate_id'  : player_id of the player's teammate}
        .ended_games [dict] : a nested dictionary of form {game_id : ended_game_info} for each ended game this player
            was involved in during the current server session. ended_game_info is itself a dictionary of form:
                {'game_id'      : game_id,
                 'role_info'    : <see role_info as defined in .active_games>,
                 'completed'    : <True if the game played out until there was a winner, False if it timed out>,
                 'result'       : <TWIML_Codenames.Game.game_result dictionary>}
        .db [pymongo database] : a pointer to the pymongo database connection
        .db_id [pymongo ObjectID] : the unique ObjectID for this player's document in the database

    Functions:
        .touch() : Called whenever a client interacts with the server to prevent them from timing out
        .return_status(gamelist) [dict] : returns the current status of the player including the status for each active
            game and a list of the game_id for each ended_game
        .new_game(game_id, game) : after a new game is created by the Gamelist object, it calls this function which adds
            the game info to the client's active_games dict
        .move_ended_game(game_id, b_completed, game_result) : after a game ends, this function is called by the Gamelist
            object. This populates the client's ended_games dict and removes it from the client's active_games dict

    Properties:
        .active [bool] : True if the client has interacted with the server more recently than the client_active_timeout
        .num_active_games [int] : the number of games the client is currently participating in
    """
    def __init__(self, player_id, db):
        """
        Instantiate a new Client

        @param player_id [int] : the unique 4-digit player identifier
        @param db [pymongo db] : a connection to the pymongo db
        """
        self.player_id = player_id
        self.last_active = datetime.now()
        self.prev_active = 0
        self.active_games = {}
        self.ended_games = {}
        self.db = db

        # Read player data from MongoDB
        result = db.players.find_one(filter={"player_id": player_id})

        if result is None: # if playerdata does not exist in MongoDB:
            # all new clients were being created with pointers to the same TWIML_codenames.Player object for some
            # reason. This deepcopy seems to have fixed it:
            self.player = deepcopy(TWIML_codenames.Player(player_id))
            player_doc = {'player_id':player_id,
                          'Elo': self.player.Elo,
                          'record': self.player.record
                          }
            self.db_id = db.players.insert_one(player_doc).inserted_id
        else:
            self.db_id = result['_id']
            # all new clients were being created with pointers to the same TWIML_codenames.Player object for some
            # reason. This deepcopy seems to have fixed it:
            self.player = deepcopy(TWIML_codenames.Player(player_id = player_id,
                                                          Elo = result['Elo'],
                                                          record = result['record'])
                                   )

    def touch(self):
        """
        Updates the .last_active and .prev_active timestamps
        """
        self.prev_active = self.last_active
        self.last_active = datetime.now()
        
    def return_status(self, gamelist):
        """
        Returns the current status of the player including the status for each active game and a list of the game_id for
            each ended_game. This is called by the @app.get(root) API call and is also called whenever a player calls an
            API function when it isn't their turn to call it. It is also returned at the end of a successfully completed
            @app.post(*) API call

        @param gamelist [TWIML_codenames_API_Server.Gamelist] : a pointer to the gamelist. Required so the
            gamelist.check_for_ended_games(game_ids_to_check) function can be called and also so the
            TWIML_codenames.Game objects can be accessed

        @returns [dict] : a nested dictionary of form {'active games' : game_statuses, 'ended games' : list[game_ids]}
            game_statuses is itself a nested dictionary of form {game_id : game_status} with game_status a dictionary of
            form:
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
        # The check for game timeouts are only called when players in that game check in:
        gamelist.check_for_ended_games(self.active_games.keys())
        
        game_statuses = {}
        for game_id, role_info in self.active_games.items():
            wait_team, wait_role, wait_player, waiting_for, wait_duration = gamelist[game_id].waiting_on_info()
            game_statuses[game_id] = {'game_id' : game_id,
                                      'game start time' : gamelist[game_id].game_start_time,
                                      'role_info' : role_info,
                                      'waiting on' : {'team' : wait_team,
                                                      'role' : wait_role,
                                                      'player_id' : wait_player,
                                                      'waiting for' : waiting_for,
                                                      'waiting duration' : wait_duration
                                                      } 
                                      }
        return {'active games' : game_statuses, 'ended games' : [x for x in self.ended_games.keys()]}
        
    def new_game(self, game_id, game):
        """
        Adds a new game to self.active_games
        When a new game is created by the gamelist, it calls this function for each client which is playing in it
        Creates and adds to self.active_games a dict of form:
            {'team'         : <1 or 2>,
             'role'         : <'spymaster' or 'operative'>,
             'teammate_id'  : player_id of the player's teammate}

        @param game_id [int] : the unique 6-digit game identifier
        @param game [TWIML_codenames.Game] : the game that was just created
        """
        if game.teams[0][0].player_id == self.player_id:
            team = 1
            role = 'spymaster'
            teammate_id = game.teams[0][1].player_id
        if game.teams[0][1].player_id == self.player_id:
            team = 1
            role = 'operative'
            teammate_id = game.teams[0][0].player_id
        if game.teams[1][0].player_id == self.player_id:
            team = 2
            role = 'spymaster'
            teammate_id = game.teams[1][1].player_id
        if game.teams[1][1].player_id == self.player_id:
            team = 2
            role = 'operative'
            teammate_id = game.teams[1][0].player_id
        self.active_games[game_id] = {'team' : team, 'role' : role, 'teammate_id' : teammate_id}

    def move_ended_game(self, game_id, b_completed, game_result):
        """
        Moves a game from self.active_games to self.ended_games
        When a game is found to have completed by the gamelist, it calls this function for each client which is playing
            in it
        Creates and adds to self.ended_games a dict of form:
            {'game_id'      : game_id,
             'role_info'    : <see role_info as defined in .active_games>,
             'completed'    : <True if the game played out until there was a winner, False if it timed out>,
             'result'       : <TWIML_Codenames.Game.game_result dictionary>}
        Then removes the game from self.active_games

        @param game_id [int] : the unique 6-digit game identifier
        @param b_completed [bool] : True if the game played out until there was a winner, False if it timed out
        @param game_result [dict] : TWIML_Codenames.Game.game_result dictionary
        """
        # Sometimes this function is called a second time after the game has already been moved. So first check if this
        # game still exists in self.active_games:
        if game_id in self.active_games.keys():
            # if the game completed, the Elo and W/L ratings will have changed, so update the MongoDB entry for this player:
            if b_completed:
                self.db.players.update_one(filter={"_id": self.db_id}, update={"$set": {'Elo': self.player.Elo}})
                self.db.players.update_one(filter={"_id": self.db_id}, update={"$set": {'record': self.player.record}})
            self.ended_games[game_id] = {'game_id' : game_id,
                                         'role_info': self.active_games[game_id],
                                         'completed': b_completed,
                                         'result': game_result
                                         }
            del self.active_games[game_id]

    @property
    def active(self):
        """
        @returns [bool] : True if the client has interacted with the server more recently than the client_active_timeout
        """
        return (datetime.now()-self.last_active < client_active_timeout)

    @property
    def num_active_games(self):
        """
        @returns [int] : the number of games the client is currently participating in
        """
        return len(self.active_games)

class Gamelist(object):
    """
    Keeps track of which games are currently in progress and stores info for those that have completed
    Individual games can be called externally via Gamelist[game_id]: see __getitem__

    Instance variables:
        .clientlist [Clientlist] : a pointer to the clientlist object for this server session
        .db [pymongo database] : a pointer to the pymongo database connection
        .active_games [dict] : a nested dictionary for each active game of form
            {game_id : {'Game object' : <TWIML_codenames.Game>,
                        'clients' : list[player_id for each client]}
            }
        .ended_games [dict] : a nested dictionary for each ended game of form
            {game_id : {'completed' : <True if the game played out until there was a winner, False if it timed out>,
                        'result' : <TWIML_Codenames.Game.game_result dictionary>}
            }
        .next_game_id [int] : the unique 6-digit integer to be used as the game_id the next time a game is created

    Functions:
        .new_game(available_clients) : creates a new game(s) and updates the client objects as necessary
        .check_for_ended_games(game_ids_to_check) : checks a list of games to see if any of them have ended
        .move_ended_game(game_id, b_completed) : moves an ended game from the active_games dict to the ended_games dict
            in the Gamelist as well as in each Client
        .is_active_game(game_id) [bool] : True if the game is active, False if it has ended
    """
    def __init__(self, clientlist):
        """
        Instantiate a new Gamelist

        @param clientlist [Clientlist] : a pointer to the clientlist object for this server session
        """
        self.clientlist = clientlist
        self.db = clientlist.db
        self.active_games = {}
        self.ended_games = {}
        self.next_game_id = \
            max([x['game_id'] for x in self.db.games.find(projection=['game_id'])] # Get list of all game_ids in the db
                +[100000] # If there aren't any game_ids yet, start at 100000
                )+1 # The next game needs to be one higher than the max

    def __getitem__(self, key):
        """
        Looks for the key in the active_games dict and then in the ended_games dict.

        If it is an active game,
            @returns [TWIML_codenames.Game] : the Game object

        If it is an ended game,
            @returns [dict] : the game outcome dict of the form:
                {'completed' : <True if the game played out until there was a winner, False if it timed out>,
                 'result' : <TWIML_Codenames.Game.game_result dictionary>}
        """
        if key in self.active_games.keys():
            return self.active_games[key]['Game object']
        elif key in self.ended_games.keys():
            return self.ended_games[key]
        # need to add error checking if game isn't in either dict

    def new_game(self, available_clients):
        """
        Creates a new game(s) with 4 clients chosen at random from the available_clients list, then adds it to
            self.active_games and populates the game to the Client objects
        If there are more than 8 clients in the available_clients list, more than one game will be created

        @param available_clients list[Client] : the queue of clients who are available to start a new game
        """
        num_new_games = len(available_clients) // 4
        random.shuffle(available_clients)
        for i in range(num_new_games):
            game_clients = available_clients[4*i:4*(i+1)]
            team1 = [client.player for client in game_clients[:2]]
            team2 = [client.player for client in game_clients[2:]]
            new_game_id = self.next_game_id
            self.next_game_id += 1
            gameboard = TWIML_codenames.Gameboard(wordlist)
            logger=MongoLogger(new_game_id, self.db)
            self.active_games[new_game_id] = {'Game object' : TWIML_codenames.Game(gameboard, team1, team2, logger),
                                              'clients' : [client.player_id for client in game_clients]
                                              }
            for client in game_clients:
                client.new_game(new_game_id, self.active_games[new_game_id]['Game object'])

    def check_for_ended_games(self, game_ids_to_check):
        """
        Checks a list of games to see if any of them have ended. Checks for both completed games and timed out games.
        If a game has ended, call .move_ended_game(game_id, b_completed) to move it from the active_games dict to the
            ended_games dict in the Gamelist as well as in each Client
        This function is called every time the .return_status() function is called for a client object. The
            game_ids_to_check are the active games for that client.

        @param game_ids_to_check list[int] : a list of the game_ids to be checked (those ids of the active games of the
            client who called this function)
        """
        game_ids_to_check = [game_id for game_id in game_ids_to_check if game_id in self.active_games.keys()]
        for game_id in game_ids_to_check:
            if self.active_games[game_id]['Game object'].game_completed:
                self.move_ended_game(game_id, b_completed=True)
            elif self.active_games[game_id]['Game object'].check_timed_out(client_active_timeout):
                self.move_ended_game(game_id, b_completed=False)

    def move_ended_game(self, game_id, b_completed):
        """
        Moves an ended game from the active_games dict to the ended_games dict in the Gamelist as well as in each Client
        Creates and adds to self.ended_games a dict of form:
            {game_id : {'completed' : <True if the game played out until there was a winner, False if it timed out>,
                        'result' : <TWIML_Codenames.Game.game_result dictionary>}
            }
        Then removes the game from self.active_games

        @param game_id [int] : the unique 6-digit game identifier
        @param b_completed [bool] : True if the game played out until there was a winner, False if it timed out
        """
        game_result = self.active_games[game_id]['Game object'].game_result
        self.ended_games[game_id] = {'completed': b_completed,
                                     'result': game_result
                                     }
        for client in self.active_games[game_id]['clients']:
            self.clientlist[client].move_ended_game(game_id, b_completed, game_result)
        del self.active_games[game_id]
        if self.clientlist.b_games_to_start:
            self.new_game(self.clientlist.available_clients)

    def is_active_game(self, game_id):
        """
        @param game_id [int] : the unique 6-digit game identifier

        @returns [bool] : True if the game is active, False if it has ended
        """
        return (game_id in self.active_games.keys())

class MongoLogger(object):
    """
    Interfaces with MongoDB to write the log for an individual game

    Instance variables:
        .game_id [int] : the unique 6-digit identifier for this game
        .db [pymongo database] : a pointer to the pymongo database connection
        .db_id [pymongo ObjectID] : the unique ObjectID for this game's document in the database

    Functions:
        .record_config(gameboard, teams) : called when a TWIML_codenames.game object is initialized. Populates starting
            info about the game to the game_log
        .set_field(field_name, val) : sets a field in the top level of the game_log
        .add_event(event_dict) : adds the event to the end of the list of events
    """
    def __init__(self, game_id, db):
        """
        Instantiate a new gamelog

        @param game_id [int] : the unique id for this game
        @param db [pymongo db] : a connection to the pymongo db
        """
        self.game_id = game_id
        self.db = db

        # Create new document in db:
        game_doc = {'game_id':game_id,
                    'in_progress':True,
                    'events':[]
                    }
        self.db_id = db.games.insert_one(game_doc).inserted_id

    def record_config(self, gameboard, teams):
        """
        called when a TWIML_codenames.game object is initialized. Populates starting info about the game to the game_log

        @param gameboard [TWIML_codenames.Gameboard] : the gameboard for this game
        @param teams [list[list[TWIML_codenames.Player]] : the list of Player objects for each of the players in each
            team
        """
        self.set_field('boardwords', [[str(x) for x in row] for row in gameboard.boardwords])
        self.set_field('boardkey', [[int(x) for x in row] for row in gameboard.boardkey])
        self.set_field('teams', {'team 1':[player.player_id for player in teams[0]],
                                 'team 2':[player.player_id for player in teams[1]]})

    def set_field(self, field_name, val):
        """
        Sets a field in the top level of the game_log

        @param field_name [str] : the key name of the field to be set
        @param val [any] : the value to be set
        """
        self.db.games.update_one(filter={"_id": self.db_id}, update={"$set": {field_name: val}})

    def add_event(self, event_dict):
        """
        Adds the event to the end of the list of events

        @param event_dict [dict] : the dictionary capturing the info associated with the event
        """
        self.db.games.update_one(filter={"_id": self.db_id}, update={"$push": {"events": event_dict}})
"""
------------------------------------------------------------------------------------------------------------------------
                                                       Functions
------------------------------------------------------------------------------------------------------------------------
"""
def validate(player_id, player_key):
    """
    @param player_id [int] : the unique 4-digit player identifier
    @param player_key [int] : the unique 8-digit key for the player

    @returns [bool] : True if the player_key is the correct one for the player_id
    """
    # Check if there is a row in player_keys that has both the player_id and the player_key. If the first dimension of
    # the resulting shape is 1, then there is and the player_key is validated:
    return player_keys.loc[(player_keys['player_id']==player_id) &
                           (player_keys['player_key']==player_key)].shape[0] == 1

def send_as_bytes(var_to_send):
    """
    converts any object (including a dict filled with various objects) into bytes to be sent via the API

    @param var_to_send [object] : the object to be encoded as bytes

    @returns [fastapi.Response] : the object encoded as bytes
    """
    return Response(content=pickle.dumps(var_to_send))

def get_leaderboards(db):
    """
    Pulls the current leaderboards from the players MongoDB

    @param db [pymongo db] : a connection to the pymongo db

    @returns leaderboards [dict] : a dict of format
        {'Spymasters' : list[(player_id,Elo)],
         'Operatives' : list[(player_id,Elo)],
         'Combined'   : list[(player_id,Elo)]}
    """
    results = db.players.find(projection=['player_id', 'Elo'])
    leaderboards = {'Spymasters': [],
                    'Operatives': [],
                    'Combined': []
                    }
    for player in results:
        player_id = player['player_id']
        Elo = player['Elo']
        leaderboards['Spymasters'].append((player_id, Elo['Spymaster']))
        leaderboards['Operatives'].append((player_id, Elo['Operative']))
        leaderboards['Combined'].append((player_id, (Elo['Spymaster'] + Elo['Operative'])/2))

    for key, leaderboard in leaderboards.items():
        leaderboards[key] = sorted(leaderboard, key=lambda k: k[1], reverse=True)

    return leaderboards

def list_player_games(player_to_pull, db):
    """
    Returns a list of game_ids for all games this player is/was involved in

    @param player_to_pull (int) : the ID of the player being queried
    @param db [pymongo db] : a connection to the pymongo db

    @returns game_ids [list[int]] : a list of the unique 6-digit ids for each game this player is/was involved in
    """
    results = db.games.find(projection=['game_id', 'teams'])
    game_ids=[]
    for game_dict in results:
        game_players = [player for team in game_dict['teams'].values() for player in team]
        if player_to_pull in game_players:
            game_ids.append(game_dict['game_id'])
    return game_ids

def list_completed_games(db):
    """
    Returns a list of game_ids for all completed games

    @param db [pymongo db] : a connection to the pymongo db

    @returns completed_game_ids [list[int]] : a list of the unique 6-digit identifiers for each completed game in the db
    """
    results = db.games.find(filter={"in_progress": False}, projection=['game_id'])
    completed_game_ids=[]
    for game_dict in results:
        completed_game_ids.append(game_dict['game_id'])
    return completed_game_ids

def pull_game_log(game_id, player_id, db):
    """
    Returns the game log for an individual game

    @param game_id [int] : the unique 6-digit identifier for this game
    @param player_id [int] : the player_id of the player pulling the log
    @param db [pymongo db] : a connection to the pymongo db

    @returns game_dict [dict] : the scrubbed game_dict
    """
    game_dict=db.games.find_one(filter={"game_id": game_id})
    if game_dict is None:
        return {'Game log not found':game_id}
    else:
        return scrub_game_log(game_dict, player_id)

def scrub_game_log(game_dict, player_id):
    """
    Removes info from the game log that would not be known to the player_id who is pulling the log

    @param game_dict [dict] : the dictionary of the document that was pulled from the mongoDB
    @param player_id [int] : the player_id of the player pulling the log

    @returns temp_dict [dict] : the scrubbed game_dict
    """

    temp_dict = deepcopy(game_dict)
    del temp_dict['_id']
    spymasters = [temp_dict['teams']['team 1'][0], temp_dict['teams']['team 2'][0]]
    operatives = [temp_dict['teams']['team 1'][1], temp_dict['teams']['team 2'][1]]

    # While game is in progress, only let the spymasters see the boardkey
    if temp_dict['in_progress'] and player_id not in spymasters:
        del temp_dict['boardkey'] # boardkey is only known by spymasters

    #remove details about illegal clues and illegal guesses except for the players who gave them
    for event in temp_dict['events']:
        # remove info about illegal clues, except for the giver of the illegal clue
        if event['event'] == 'clue_given': # only interested in clue_given events
            if event['legal_clue'] != 'Yes': # only interested in illegal clues
                # only scrub the illegal clue if the player_id doesn't match the spymaster for this event
                if player_id != spymasters[event['team_num']-1]:
                    del event['clue_word']
                    del event['clue_count']
                    event['legal_clue'] = 'Illegal clue given' # overwrite the explanation of why the clue was illegal

        # remove info about illegal guesses, except for the giver of the illegal guess
        if event['event'] == 'guess skipped: guess not in unguessed_words':
            # only scrub the illegal guess if the player_id doesn't match the operative for this event
            if player_id != operatives[event['team_num'] - 1]:
                del event['word_guessed']

    return temp_dict
"""
------------------------------------------------------------------------------------------------------------------------
                                                    Global Variables
------------------------------------------------------------------------------------------------------------------------
"""
client_active_timeout = timedelta(minutes = 5)
min_clients_to_start_new_game = 6 # needs to be >4 or a new game will start with the same players each time a game ends
max_active_games_per_player = 1
# load the list of words from which the gameboards will randomly select 25 words when generated:
wordlist = [line.strip() for line in open('wordlist.txt', 'r').readlines()]
player_keys = pd.read_csv('player_keys.csv')