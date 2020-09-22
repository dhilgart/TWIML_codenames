"""
TWIML_codenames_API_Server.py: containing functions called by the server for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""

import TWIML_codenames
from datetime import datetime, timedelta
from fastapi import Response
import pickle
import json
import os.path
import random

client_active_timeout = timedelta(minutes = 5)
min_clients_to_start_new_game = 6 # needs to be >4 or else a new game will start with the same players each time a game ends
max_active_games_per_player = 1
wordlist = [line.strip() for line in open('wordlist.txt', 'r').readlines()]

class clientlist(object):
    """
    Keeps track of which clients are currently actively interacting with the server
    <Document functions, properties (including self.* variables), methods, etc. here>
    """
    def __init__(self):
        self.clients = {}

    def __getitem__(self, key):
        return self.clients[key]
    
    def client_touch(self, player_id):
        """
        Updates the last_active timestamp for the user
        Called whenever a client sends any get or post to the server
        """
        if player_id in self.clients.keys():
            self.clients[player_id].touch()
        else:
            self.add_client(self, player_id)

    def add_client(self, player_id):
        """
        Creates a new client object and adds it to the self.clients dict
        """
        self.clients[player_id] = client(player_id)

    @property
    def active_clients(self):
        """
        Returns a list of all the clients that are currently active (those who have interacted with the server in any 
            way within the client_active_timeout duration)
        """
        active_clients = [client for client in self.clients.values() if client.active]
        return active_clients

    @property
    def available_clients(self):
        """
        Returns a list of currently active clients who aren't involved in a game already
        """
        available_clients = [client for client in self.active_clients 
                             if client.num_active_games < max_active_games_per_player]
        return available_clients

    @property
    def b_games_to_start(self):
        """
        Boolean: Are there enough available clients to start a new game?
        """
        return len(self.available_clients) >= min_clients_to_start_new_game

class client(object):
    """
    Stores info about an individual client
    """
    def __init__(self, player_id):
        self.player_id = player_id
        self.last_active = datetime.now()
        self.prev_active = 0
        self.active_games = {}
        self.ended_games = {}

        # When creating a new client object, check whether the player exists in the playerlist.
        if player_id not in playerlist.keys():
            # If not, create a Player object and add it to the playerlist:
            playerlist[player_id] = TWIML_codenames.Player(player_id)
            # Then update the playerlist on disk:
            write_playerlist()

    def touch(self):
        self.prev_active = self.last_active
        self.last_active = datetime.now()
        
    def return_status(self, gamelist):
        """
        
        """
        self.check_for_ended_games()
        
        game_statuses = {}
        for game_id, role_info in self.active_games:
            wait_team, wait_role, wait_player, waiting_for, wait_duration = gamelist[game_id].waiting_on()
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
        return {'active games' : game_statuses, 'ended games' : self.ended_games}
        
    def new_game(self, game_id, game):
        if game.team1[0].player_id == self.player_id:
            team = 1
            role = 'spymaster'
            teammate_id = game.team1[1].player_id
        if game.team1[1].player_id == self.player_id:
            team = 1
            role = 'operative'
            teammate_id = game.team1[0].player_id
        if game.team2[0].player_id == self.player_id:
            team = 2
            role = 'spymaster'
            teammate_id = game.team2[1].player_id
        if game.team2[1].player_id == self.player_id:
            team = 2
            role = 'operative'
            teammate_id = game.team2[0].player_id
        self.active_games[game_id] = {'team' : team, 'role' : role, 'teammate_id' : teammate_id}
    
    def check_for_ended_games(self, gamelist):
        """
        
        """
        for game_id, role_info in self.active_games:
            if gamelist[game_id].game_end:
                self.ended_games[game_id] = {'game_id' : game_id,
                                             'role_info' : role_info,
                                             'completed' : True,
                                             'result' : gamelist[game_id].game_result
                                             }
                del self.active_games[game_id]
            #elif game timed out:
            #    del self.active_games[game_id]

    @property
    def active(self):
        return (datetime.now()-self.last_active < client_active_timeout)

    @property
    def num_active_games(self):
        return len(self.active_games)

class gamelist(object):
    """
    Keeps track of which games are currently in progress
    """
    def __init__(self):
        self.games = {}

    def __getitem__(self, key):
        return self.games[key]

    def new_game(self, available_clients):
        """
        Creates a new game(s) with 4 clients chosen at random from the available_clients list
        If there are more than 8 clients in the available_clients list, more than one game will be created
        """
        num_new_games = len(available_clients) // 4
        random.shuffle(available_clients)
        for i in range(num_new_games):
            game_clients = available_clients[4*i:4*(i+1)]
            team1 = [playerlist[client.player_id] for client in game_clients[:2]]
            team2 = [playerlist[client.player_id] for client in game_clients[2:]]
            new_game_id = max(self.games.keys())+1
            gameboard = TWIML_codenames.gameboard(wordlist)
            self.games[new_game_id] = TWIML_codenames.Game(gameboard, team1, team2)
            for client in game_clients:
                client.new_game(new_game_id, self.games[new_game_id])


def validate(player_id, player_key):
    """

    """

    return True


def send_as_bytes(var_to_send):
    return Response(content=pickle.dumps(var_to_send))


def write_playerlist():
    """

    """
    playerlist_dump = {player.player_id : {'Elo':player.Elo, 'record':player.record} for player in playerlist.values()}
    json.dump(playerlist_dump, open('playerlist.txt', 'w'))

def read_playerlist():
    """

    """
    if os.path.exists('playerlist.txt'):
        player_data = json.load(open('playerlist.txt', 'r'))
        playerlist = {int(player_id) : TWIML_codenames.Player(int(player_id), pdata['Elo'], pdata['record']) for player_id, data in player_data.items()}
    else:
        playerlist = {}
    return playerlist

playerlist = read_playerlist()