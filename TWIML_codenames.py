"""
TWIML_codenames.py: Module to simulate games for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
"""
import nltk
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
import numpy as np
from datetime import datetime, timedelta
from copy import deepcopy

class Gameboard(object):
    """
    A gameboard object containing the 5x5 grid of words for the current game, the key for which words belong to which
        team, and a boardmarkers array that tracks which words have been guessed so far
    """
    def __init__(self, wordlist):
        """
        Instantiate a new gameboard
        @param wordlist (list[str]): the list of words from which to generate the board

        boardwords (5x5 np.array[str]): the 5x5 grid of words. Remains unchanged after initialization
        boardkey (5x5 np.array[int]): the key that tells which words belong to which team. Remains unchanged after
            initialization. (1 = team 1, 2 = team 2, 0 = neutral, -1 = assassin)
        boardmarkers (5x5 np.array[float]): the array that tracks which words have been tapped and what was revealed.
            Starts as an array of np.NaNs. As words are tapped (guessed), the values from the boardkey are added for
            each tapped word.
        """
        self.boardwords = self.generate_board(wordlist)
        self.boardmarkers = np.zeros((5,5))
        self.boardmarkers[:] = np.NaN
        self.boardkey = self.generate_key()

    def generate_board(self, wordlist):
        """
        Generates the array and fills it with a random subset of words from the wordlist
        @param wordlist (list[str]): the list of words from which to generate the board
        @returns words (5x5 np.array): the board of words
        """
        words = np.random.choice(wordlist, size=(5,5), replace=False)
        return words

    def generate_key(self):
        """
        Creates the key of which locations belong to which team
         1 = team 1
         2 = team 2
         0 = neutral
        -1 = assassin
        """
        boardkey = np.zeros(25, dtype=int)
        boardkey[:9] = 1 #team 1's words (9x)
        boardkey[9:9 + 8] = 2 #team 2's words (8x)
        boardkey[-1] = -1 #assassin word (1x)
        #remaining zeros are innocent bystander words (7x)
        np.random.shuffle(boardkey)
        boardkey=np.reshape(boardkey,(5,5))
        return boardkey

    def tap(self,word):
        """
        Executed when a player taps a word
        @param word (str): the word to be tapped
        @returns team (int): the team of the tapped word
            (1 = team 1, 2 = team 2, 0 = neutral, -1 = assassin)
        """
        x_loc, y_loc = self.word_loc(word)
        team = self.boardkey[x_loc,y_loc]
        self.boardmarkers[x_loc,y_loc]=team
        return team

    def word_loc(self,word):
        """
        returns the x, y location of the word
        @param word (str): the word to be located
        @returns x_loc, y_loc (int, int)
        """
        #Add error handling for guess word does not exist or already tapped
        x_loc, y_loc = np.where(self.boardwords == word)
        return x_loc[0], y_loc[0]

    def unguessed_words(self, team_num=np.NaN):
        """
        @param team_num (int): (optional) the team number for which to list the remaining words. If not supplied, or
            np.NaN, will return all remaining words
        @returns unguessed_words (list[str]): a list of the words that have not yet been guessed
        """
        if np.isnan(team_num):
            return self.boardwords[np.isnan(self.boardmarkers)]
        else:
            return self.boardwords[(self.boardkey==team_num) & (np.isnan(self.boardmarkers))]

    def remaining(self,team_num):
        """
        Counts how many cards are left for the given team
        @param team_num (int): the team number for which to count the remaining cards
        @returns count (int): number of remaining cards for that team
        """
        return sum(sum(self.boardkey==team_num))-sum(sum(self.boardmarkers==team_num))


class Game(object):
    """
    The object for running a game of codenames. Contains the mechanics of the game
    """
    def __init__(self, gameboard, team1, team2):
        """
        Instantiate a new game
        @param gameboard (Gameboard): the gameboard on which this game will be played. Must be instantiated prior to
            instantiating the game
        @param team1 (list[Player]): a list of Player objects containing the necessary info for each player on team1.
            team1[0] is the spymaster and team1[1] is the operative (guesser)
        @param team2 (list[Player]): a list of Player objects containing the necessary info for each player on team2.
            team2[0] is the spymaster and team2[1] is the operative (guesser)
        """
        self.gameboard = gameboard
        self.teams = [team1, team2]
        self.spymasters = [team1[0], team2[0]]
        self.operatives = [team1[1], team2[1]]
        self.curr_team = 1
        self.not_curr_team = 2
        self.waiting_on = 'spymaster'
        self.waiting_query_since = datetime.now()
        self.waiting_inputs_since = datetime(2020,1,1)
        self.curr_clue_word = ''
        self.curr_clue_count = -1
        self.game_completed = False #Used to track whether the end of the game has been reached yet
        self.game_timed_out = False
        self.game_result = {}
        self.game_start_time = datetime.now()

    def solicit_clue_inputs(self):
        """
        Returns the inputs to be used by the spymaster's generate_clue(team_num, gameboard) function
        Called when the spymaster sends a get command to root+"{game_id}/generate_clue/"
        Verification that it is the requesting player's turn takes place before this function is called
        """
        self.waiting_inputs_since = datetime.now()
        
        return self.curr_team, self.gameboard

    def clue_given(self, clue_word, clue_count):
        """
        Takes the clue_word and clue_count from the spymaster and updates the game status accordingly
        Called when the spymaster sends a post command to root+"{game_id}/generate_clue/"
        Verification that it is the requesting player's turn takes place before this function is called
        """
        if self.legal_clue(clue_word):
            self.curr_clue_word = clue_word
            self.curr_clue_count = clue_count
            self.waiting_on = 'operative'
            self.waiting_query_since = datetime.now()
        else: # if the clue word was illegal, end the current turn
            self.switch_teams()
            self.waiting_on = 'spymaster'
            self.waiting_query_since = datetime.now()

    def solicit_guesses_inputs(self):
        """
        Returns the inputs to be used by the operative's generate_guesses(team_num, clue_word, clue_count,
            unguessed_words, boardwords, boardmarkers) function
        Called when the operative sends a get command to root+"{game_id}/generate_guesses/"
        Verification that it is the requesting player's turn takes place before this function is called
        """
        team_num = self.curr_team
        clue_word = self.curr_clue_word
        clue_count = self.curr_clue_count
        unguessed_words = self.gameboard.unguessed_words()
        boardwords = self.gameboard.boardwords
        boardmarkers = self.gameboard.boardmarkers

        self.waiting_inputs_since = datetime.now()
        
        return team_num, clue_word, clue_count, unguessed_words, boardwords, boardmarkers

    def guesses_given(self, guesses):
        """
        Takes the gueses from the operative and updates the game status accordingly
        Called when the operative sends a post command to root+"{game_id}/generate_guesses/"
        Verification that it is the requesting player's turn takes place before this function is called
        """
        # If the spymaster specified a clue for 0 or infinity (infinity is represented by 10):
        if (self.curr_clue_count == 0) | (self.curr_clue_count == 10):
            num_guesses = len(guesses)
        else:
            num_guesses = min(self.curr_clue_count + 1, len(guesses))

        for i in range(num_guesses):
            result = self.gameboard.tap(guesses[i])
            self.check_game_over(result)
            if self.game_completed:
                break # if the game is over, no need to continue guessing
            if result != self.curr_team:
                break  # if a guess is not correct, stop guessing by breaking out of this for loop
        self.switch_teams()
        self.waiting_on = 'spymaster'
        self.waiting_query_since = datetime.now()

    def legal_clue(self, clue_word):
        """
        Checks if the clue provided by the spymaster is a legal clue
        @param clue_word (str): the clue word provided by the spymaster
        @returns legal_clue(bool): True if the clue is legal, False if illegal
        """
        unguessed_words=self.gameboard.unguessed_words()

        #Check partial words:
        for word in unguessed_words:
            if clue_word in word:
                return False
            if word in clue_word:
                return False

        #Check Lemmas
        illegal_lemmas=set()
        for word in unguessed_words:
            for pos in ['n',  # noun
                        'v',  # verb
                        'a',  # adjective
                        's',  # adjective satellite
                        'r'   # adverb
                        ]:
                illegal_lemmas.add(wordnet_lemmatizer.lemmatize(word, pos=pos))

        for pos in ['n',  # noun
                    'v',  # verb
                    'a',  # adjective
                    's',  # adjective satellite
                    'r'  # adverb
                    ]:
            if wordnet_lemmatizer.lemmatize(clue_word, pos=pos) in illegal_lemmas:
                return False

        #If has not returned False by now, it has passed all the tests
        return True

    def check_game_over(self, result):
        """
        Checks to see if one of the conditions has been met to end the game. If so, updates game_completed to true and
            populates game_result dict
        @param result (int): the team of the most recently tapped word. Used to check if the Assassin has been tapped
        """
        if result == -1:  # If the operative guessed the assassin word
            self.game_completed = True
            self.game_result['winning team'] = {'num' : self.not_curr_team}
            self.game_result['losing team'] = {'num' : self.curr_team}
        elif self.gameboard.remaining(self.curr_team) == 0: #if the current team has no words left to guess
            self.game_completed = True
            self.game_result['winning team'] = {'num' : self.curr_team}
            self.game_result['losing team'] = {'num' : self.not_curr_team}
        elif self.gameboard.remaining(self.not_curr_team) == 0: #if the other (not-current) team has no words left to guess
            self.game_completed = True
            self.game_result['winning team'] = {'num' : self.not_curr_team}
            self.game_result['losing team'] = {'num' : self.curr_team}

        if self.game_completed:
            for team_dict in self.game_result.values():
                players = []
                for player in self.teams[team_dict['num']-1]:
                    players.append({'player_id' : player.player_id,
                                    'Elo before update' : deepcopy(player.Elo)
                                    })
                team_dict['players'] = players
            self.game_result['start time'] = self.game_start_time
            self.game_result['end time'] = datetime.now()
            self.game_result['final gameboard'] = self.gameboard

            self.update_ratings()

            for i, team in enumerate(self.teams):
                if i == self.game_result['winning team']['num']-1:
                    team_key = 'winning team'
                else:
                    team_key = 'losing team'

                for j, player in enumerate(team):
                    self.game_result[team_key]['players'][j]['Elo after update'] = deepcopy(player.Elo)

    def switch_teams(self):
        """
        Switches the active team
        """
        if self.curr_team == 1:
            self.curr_team = 2
            self.not_curr_team = 1
        else:
            self.curr_team = 1
            self.not_curr_team = 2

    def update_ratings(self):
        """
        Calls the appropriate functions to update the players' Elo ratings and W/L records for all players
        """
        avg_starting_Elo = [(self.spymasters[0].Elo['Spymaster'] + self.operatives[0].Elo['Operative']) / 2,
                            (self.spymasters[1].Elo['Spymaster'] + self.operatives[1].Elo['Operative']) / 2
                            ]

        for i, player in enumerate(self.spymasters):
            not_i = (i == 0)*1 #1 if i = 0, 0 otherwise
            player.update_ratings(role = 'Spymaster',
                                  result = (i+1 == self.game_result['winning team']['num'])*1,
                                  own_team_avg_Elo = avg_starting_Elo[i],
                                  opp_team_avg_Elo = avg_starting_Elo[not_i])
        for i, player in enumerate(self.operatives):
            not_i = (i == 0)*1 #1 if i = 0, 0 otherwise
            player.update_ratings(role = 'Operative',
                                  result = (i+1 == self.game_result['winning team']['num'])*1,
                                  own_team_avg_Elo = avg_starting_Elo[i],
                                  opp_team_avg_Elo = avg_starting_Elo[not_i])

    def waiting_on_info(self):
        """

        """
        wait_team = self.curr_team
        wait_role = self.waiting_on
        if self.waiting_on == 'spymaster':
            wait_player = self.spymasters[self.curr_team-1]
        else:
            wait_player = self.operatives[self.curr_team - 1]
        if self.waiting_query_since > self.waiting_inputs_since:  # If waiting_query_since reset more recently than waiting_inputs_since
            waiting_for = 'query'
            wait_duration = datetime.now() - self.waiting_query_since
        else:
            waiting_for = 'input'
            wait_duration = datetime.now() - self.waiting_inputs_since
        return wait_team, wait_role, wait_player.player_id, waiting_for, wait_duration

    def check_timed_out(self, max_duration):
        wait_team, wait_role, wait_player, waiting_for, wait_duration = self.waiting_on_info()
        if wait_duration > max_duration:
            self.game_timed_out = True
            self.game_result = {'timed out waiting on': {'team': wait_team,
                                                         'role': wait_role,
                                                         'player_id': wait_player,
                                                         'waiting for': waiting_for,
                                                         'waiting duration': wait_duration
                                                         },
                                'teams' : {1 : [{'player_id' : player.player_id} for player in self.teams[0]],
                                           2 : [{'player_id' : player.player_id} for player in self.teams[1]]
                                           },
                                'start time' : self.game_start_time,
                                'end time' : datetime.now(),
                                'final gameboard' : self.gameboard
                                }
        return self.game_timed_out

class Player(object):
    """
    An object containing all the info needed to track the player's performance
    """
    def __init__(self, player_id, Elo = {'Spymaster': 1500., 'Operative': 1500.},
                 record = {'Spymaster': {'W': 0, 'L': 0}, 'Operative': {'W': 0, 'L': 0}}):
        """
        @param player_id (int): the unique id for the current player
        @param files_location (str): the path to the folder where this player's files are stored
        @param model_filename (str): the name of the file for the model to be used for this player
        """
        self.player_id = player_id
        self.Elo = Elo
        self.record = record

    def update_ratings(self, role, result, own_team_avg_Elo, opp_team_avg_Elo):
        """
        Updates the win/loss record and Elo rating of the player
        @param role (str): 'Spymaster' or 'Operative'
        @param result (int): 1 for win, 0 for loss
        @param own_team_avg_Elo (dbl): the avg Elo rating of the player's team
        @param opp_team_avg_Elo (dbl): the avg Elo rating of the opponents' team
        """
        if result == 1:
            record_key = 'W'
        else:
            record_key = 'L'
        self.record[role][record_key] += 1
        self.Elo[role] += self.calc_delta_Elo(result, own_team_avg_Elo, opp_team_avg_Elo)

    def calc_delta_Elo(self, result, own_team_avg_Elo, opp_team_avg_Elo):
        """
        Calculates the change in Elo rating of the player
        @param result (int): 1 for win, 0 for loss
        @param own_team_avg_Elo (dbl): the avg Elo rating of the player's team
        @param opp_team_avg_Elo (dbl): the avg Elo rating of the opponents' team
        @returns delta_Elo (dbl): the amount the player's Elo should change as a result of the outcome
        """
        k=20

        expected_score = 1 / (1 + \
                              10**((opp_team_avg_Elo - own_team_avg_Elo)/400)
                              )
        delta_Elo = k * (result - expected_score)
        return delta_Elo

def is_players_turn(game, player_id):
    """

    """
    if game.waiting_on == 'spymaster':
        waiting_on_player_id = game.spymasters[game.curr_team - 1].player_id
    else:
        waiting_on_player_id = game.operatives[game.curr_team - 1].player_id
    return player_id == waiting_on_player_id
