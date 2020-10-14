"""
TWIML_codenames.py: Module to simulate games for TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>

Contains 4 class definitions:
    Gameboard : Contains the 5x5 grid of words for the current game, the key for which words belong to which team, and a
        boardmarkers array that tracks which words have been guessed so far
    Game : Contains the mechanics of the game
    LocalLogger : The default logger if no logger is provided when a game is instantiated. Records a log of all the
        actions taken in a game
    Player : Contains all the info needed to track the player's performance
"""

"""
------------------------------------------------------------------------------------------------------------------------
                                                         To Do
------------------------------------------------------------------------------------------------------------------------
    - 
"""

"""
------------------------------------------------------------------------------------------------------------------------
                                                        Imports
------------------------------------------------------------------------------------------------------------------------
"""
import nltk
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
import numpy as np
from datetime import datetime, timedelta
from copy import deepcopy

"""
------------------------------------------------------------------------------------------------------------------------
                                                        Classes
------------------------------------------------------------------------------------------------------------------------
"""
class Gameboard(object):
    """
    A gameboard object containing the 5x5 grid of words for the current game, the key for which words belong to which
        team, and a boardmarkers array that tracks which words have been guessed so far

    Instance variables:
        .boardwords [5x5 np.array[str]] : the 5x5 grid of words. Remains unchanged after initialization
        .boardkey [5x5 np.array[int]] : the key that tells which words belong to which team. Remains unchanged after
            initialization. (1 = team 1, 2 = team 2, 0 = neutral, -1 = assassin)
        .boardmarkers [5x5 np.array[float]] : the array that tracks which words have been tapped and what was revealed.
            Starts as an array of np.NaNs. As words are tapped (guessed), the values from the boardkey are added for
            each tapped word.
    Functions:
        .generate_board(wordlist) [5x5 np.array[str]] : Generates the array and fills it with a random subset of words
            from the wordlist
        .generate_key() [5x5 np.array[int]]: Creates the key of which locations belong to which team
        .tap(word) [int] : Executed when a player taps a word, returns the team that word belongs to
        .word_loc(word) [int, int] : returns the x, y location of the word
        .unguessed_words(team_num) [list[str]] : returns a list of the words that have not yet been guessed
        .remaining(team_num) [int] : Counts how many cards are left for the given team
    """
    def __init__(self, wordlist):
        """
        Instantiate a new gameboard
        generates a new board by randomly placing 25 words from the wordlist
        generates a new boardkey at random
        generates boardmarkers array and populates it with np.NaNs

        @param wordlist (list[str]): the list of words from which to generate the board
        """
        self.boardwords = self.generate_board(wordlist)
        self.boardkey = self.generate_key()
        self.boardmarkers = np.zeros((5,5))
        self.boardmarkers[:] = np.NaN

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

        @returns boardkey [5x5 np.array[int]] : the key that tells which words belong to which team.
        """
        boardkey = np.zeros(25, dtype=int)
        boardkey[:9] = 1 #team 1's words (9x)
        boardkey[9:9 + 8] = 2 #team 2's words (8x)
        boardkey[-1] = -1 #assassin word (1x)
        #remaining zeros are innocent bystander words (7x)
        np.random.shuffle(boardkey)
        boardkey=np.reshape(boardkey,(5,5))
        return boardkey

    def tap(self, word):
        """
        Executed when a player taps a word

        @param word (str): the word to be tapped

        @returns team (int): the team of the tapped word
            (1 = team 1, 2 = team 2, 0 = neutral, -1 = assassin)
        """
        x_loc, y_loc = self.word_loc(word)
        team = self.boardkey[x_loc,y_loc]
        self.boardmarkers[x_loc,y_loc]=team
        return int(team) # convert from numpy.int64 to regular python int so it can be stored in the mongoDB

    def word_loc(self, word):
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
            np_words = self.boardwords[np.isnan(self.boardmarkers)]
        else:
            np_words = self.boardwords[(self.boardkey==team_num) & (np.isnan(self.boardmarkers))]
        return [word for word in np_words] # convert from np.array to list

    def remaining(self, team_num):
        """
        Counts how many cards are left for the given team

        @param team_num (int): the team number for which to count the remaining cards

        @returns count (int): number of remaining cards for that team
        """
        return sum(sum(self.boardkey==team_num))-sum(sum(self.boardmarkers==team_num))


class Game(object):
    """
    The object for running a game of codenames. Contains the mechanics of the game

    Instance variables:
        .gameboard [TWIML_codenames.Gameboard] : the gameboard object for this game
        .teams [list[list[TWIML_codenames.Player]]] : stores the list of Player objects for each of the players in each
            team
        .curr_team [int] : tracks which team's turn it is
        .waiting_on [str] : is the game waiting on the spymaster or the operative?
        .waiting_query_since [datetime] : the game has been waiting for the current player to query the server since
            this timestamp
        .waiting_inputs_since [datetime] : the game has been waiting for the current player to return inputs to the
            server since this timestamp
        .curr_clue_word [str] : the latest clue word provided by the most recent spymaster
        .curr_clue_count [int] : the latest clue count provided by the most recent spymaster
        .game_completed [bool] : used to track whether the end of the game has been reached yet
        .game_timed_out [bool] : used to track whether the game has timed out
        .game_result [dict] : a nested dict containing the info for the result of the game. Can take two forms:
            if the game timed out it takes the form:
                {'timed out waiting on': {'team': <1 or 2>,
                                          'role': <'spymaster' or 'operative'>,
                                          'player_id': player_id of the player who timed out,
                                          'waiting for': <'query' or 'input'>,
                                          'waiting duration': [timedelta]
                                         },
                 'teams' : {1 : [{'player_id' : player_id} for player on team 1],
                            2 : [{'player_id' : player_id} for player on team 2]
                            },
                 'start time' : [datetime],
                 'end time' : [datetime],
                 'final gameboard' : TWIML_codenames.Gameboard object
                }
            if the game completed it takes the form:
                {'winning team' : {'num' : team number,
                                   'players' : list[player_info]
                                  },
                 'losing team'  : {'num' : team number,
                                   'players' : list[player_info]
                                  },
                 'start time' : [datetime],
                 'end time' : [datetime],
                 'final gameboard' : TWIML_codenames.Gameboard object
                }
                where player_info is a dict of form {'player_id' : player_id,
                                                     'Elo before update' : {'Spymaster': [float],
                                                                            'Operative': [float]},
                                                     'Elo after update'  : {'Spymaster': [float],
                                                                            'Operative': [float]}}
        .game_start_time [datetime] : when the game started
        .logger [TWIML_codenames_API_Server.MongoLogger or LocalLogger] : the object that records the log and either
            stores it in local memory (LocalLogger) or in the mongoDB (MongoLogger)

    Properties:
        .spymasters [list[list[TWIML_codenames.Players]]] : a list of the player objects for just the spymasters
        .operatives [list[list[TWIML_codenames.Players]]] : a list of the player objects for just the operatives
        .not_curr_team [int] : the team number of the team who isn't the current team

    Functions:
        .solicit_clue_inputs() [team_num, gameboard] : Returns the inputs to be used by the spymaster's generate_clue
            function. Called when the spymaster sends a get command to root+"{game_id}/generate_clue/"
        .clue_given(clue_word, clue_count) : Takes the clue_word and clue_count from the spymaster and updates the game
            status accordingly. Called when the spymaster sends a post command to root+"{game_id}/generate_clue/"
        .solicit_guesses_inputs() [team_num, clue_word, clue_count, unguessed_words, boardwords, boardmarkers] : Returns
            the inputs to be used by the operative's generate_guesses function. Called when the operative sends a get
            command to root+"{game_id}/generate_guesses/"
        .guesses_given(guesses) : Takes the gueses from the operative and updates the game status accordingly. Called
            when the operative sends a post command to root+"{game_id}/generate_guesses/"
        .legal_clue(clue_word) [bool, str] : Checks if the clue provided by the spymaster is a legal clue and if not,
            provides an explanation why not
        .check_game_over(result) :  Checks to see if one of the conditions has been met to end the game. If so, updates
            game_completed to True and populates game_result dict
        .switch_teams() : Switches the active team
        .update_ratings() : Calls the appropriate functions to update the players' Elo ratings and W/L records for all
            players
        .waiting_on_info() [wait_team, wait_role, wait_player_id, waiting_for, wait_duration] : Returns info about who
            the game is waiting on including:
                wait_team = <1 or 2>
                wait_role = <'spymaster' or 'operative'>
                wait_player_id = player_id of the player being waited on
                waiting_for = <'query' or 'input'>
                wait_duration = [timedelta]
        .is_players_turn(player_id) [bool] : Checks if it is the turn of player_id
        .check_timed_out(max_duration) [bool] : Checks if the player being waited on has timed out. If so, updates
            game_result dict accordingly.
        .log_end_of_game : Adds elements from self.game_result to the game log. Called when either the game completes or
            times out.
    """
    def __init__(self, gameboard, team1, team2, logger=None):
        """
        Instantiate a new game

        @param gameboard (Gameboard): the gameboard on which this game will be played. Must be instantiated prior to
            instantiating the game
        @param team1 (list[Player]): a list of Player objects containing the necessary info for each player on team1.
            team1[0] is the spymaster and team1[1] is the operative (guesser)
        @param team2 (list[Player]): a list of Player objects containing the necessary info for each player on team2.
            team2[0] is the spymaster and team2[1] is the operative (guesser)
        @param gamelog [TWIML_codenames.GameLog] : The gamelog for this game
        """
        self.gameboard = gameboard
        self.teams = [team1, team2]
        self.curr_team = 1
        self.waiting_on = 'spymaster'
        self.waiting_query_since = datetime.utcnow()
        self.waiting_inputs_since = datetime(2020,1,1)
        self.curr_clue_word = ''
        self.curr_clue_count = -1
        self.game_completed = False #Used to track whether the end of the game has been reached yet
        self.game_timed_out = False
        self.game_result = {}
        self.game_start_time = datetime.utcnow()

        if logger is None:
            self.logger = LocalLogger()
        else:
            self.logger = logger
        self.logger.record_config(gameboard, self.teams)

    @property
    def spymasters(self):
        return [self.teams[0][0], self.teams[1][0]]

    @property
    def operatives(self):
        return [self.teams[0][1], self.teams[1][1]]

    @property
    def not_curr_team(self):
        if self.curr_team == 1:
            return 2
        else:
            return 1

    def solicit_clue_inputs(self):
        """
        Returns the inputs to be used by the spymaster's generate_clue(team_num, gameboard) function
        Called when the spymaster sends a get command to root+"{game_id}/generate_clue/"
        Verification that it is the requesting player's turn takes place before this function is called

        @returns team_num [int] : the player's team number <1 or 2>
        @returns gameboard [TWIML_codenames.Gameboard] : the current gameboard
        """
        self.waiting_inputs_since = datetime.utcnow()
        
        return self.curr_team, self.gameboard

    def clue_given(self, clue_word, clue_count):
        """
        Takes the clue_word and clue_count from the spymaster and updates the game status accordingly
        Called when the spymaster sends a post command to root+"{game_id}/generate_clue/"
        Verification that it is the requesting player's turn takes place before this function is called

        @param clue_word [str] : the clue word
        @param clue_count [int] : the clue count
        """
        bLegal, explanation = self.legal_clue(clue_word)
        self.logger.add_event({'event': 'clue_given',
                               'timestamp': datetime.utcnow(),
                               'team_num': self.curr_team,
                               'clue_word': clue_word,
                               'clue_count': clue_count,
                               'legal_clue': explanation
                               })
        if bLegal:
            self.curr_clue_word = clue_word
            self.curr_clue_count = clue_count
            self.waiting_on = 'operative'
            self.waiting_query_since = datetime.utcnow()
        else: # if the clue word was illegal, end the current turn
            self.logger.add_event({'event': 'end guessing',
                                   'timestamp': datetime.utcnow(),
                                   'reason': 'illegal clue given; no guessing allowed'
                                   })
            self.switch_teams()
            self.waiting_on = 'spymaster'
            self.waiting_query_since = datetime.utcnow()

    def solicit_guesses_inputs(self):
        """
        Returns the inputs to be used by the operative's generate_guesses(team_num, clue_word, clue_count,
            unguessed_words, boardwords, boardmarkers) function
        Called when the operative sends a get command to root+"{game_id}/generate_guesses/"
        Verification that it is the requesting player's turn takes place before this function is called

        @returns team_num [int] : the player's team number <1 or 2>
        @returns clue_word [str] : the clue word given by the player's spymaster
        @returns clue_count [int] : the clue count given by the player's spymaster
        @returns unguessed_words list[str] : the 1-D list of words on the board that have not yet been guessed
        @returns boardwords [5x5 np.array[str]] : the 5x5 grid of words
        @returns boardmarkers [5x5 np.array[float]] : the array that tracks which words have been tapped and what was
            revealed. Starts as an array of np.NaNs. As words are tapped (guessed), the values from the boardkey are
            added for each tapped word.
        """
        team_num = self.curr_team
        clue_word = self.curr_clue_word
        clue_count = self.curr_clue_count
        unguessed_words = self.gameboard.unguessed_words()
        boardwords = self.gameboard.boardwords
        boardmarkers = self.gameboard.boardmarkers

        self.waiting_inputs_since = datetime.utcnow()
        
        return team_num, clue_word, clue_count, unguessed_words, boardwords, boardmarkers

    def guesses_given(self, guesses):
        """
        Takes the gueses from the operative and updates the game status accordingly
        Called when the operative sends a post command to root+"{game_id}/generate_guesses/"
        Verification that it is the requesting player's turn takes place before this function is called

        @param guesses list[str] : list of the guesses the player wants to make
        """
        if len(guesses) == 0:
            self.logger.add_event({'event': 'end guessing',
                                   'timestamp': datetime.utcnow(),
                                   'reason': 'Zero guesses provided'
                                   })

        # If the spymaster specified a clue for 0 or infinity (infinity is represented by 10):
        if (self.curr_clue_count == 0) | (self.curr_clue_count == 10):
            num_guesses = len(guesses)
        else:
            num_guesses = min(self.curr_clue_count + 1, len(guesses))

        for i in range(num_guesses):
            # check if the guess word exists in the unguessed_words list. If not, move on to the next word in the list
            if guesses[i] in self.gameboard.unguessed_words():
                result = self.gameboard.tap(guesses[i])
                self.logger.add_event({'event': 'guess made',
                                       'timestamp': datetime.utcnow(),
                                       'team_num': self.curr_team,
                                       'word_guessed': guesses[i],
                                       'result': result
                                       })
                self.check_game_over(result)
                if self.game_completed:
                    break # if the game is over, no need to continue guessing
                if result != self.curr_team:
                    self.logger.add_event({'event': 'end guessing',
                                           'timestamp': datetime.utcnow(),
                                           'reason': 'incorrect guess made'
                                           })
                    break # if a guess is not correct, stop guessing by breaking out of this for loop
            else:
                self.logger.add_event({'event': 'guess skipped: guess not in unguessed_words',
                                       'timestamp': datetime.utcnow(),
                                       'team_num': self.curr_team,
                                       'word_guessed': guesses[i]
                                       })
            if i == len(guesses)-1:
                self.logger.add_event({'event': 'end guessing',
                                       'timestamp': datetime.utcnow(),
                                       'reason': 'no more guesses provided'
                                       })
            elif i == self.curr_clue_count:
                self.logger.add_event({'event': 'end guessing',
                                       'timestamp': datetime.utcnow(),
                                       'reason': 'num guesses provided exceeded clue_count+1'
                                       })
        self.switch_teams()
        self.waiting_on = 'spymaster'
        self.waiting_query_since = datetime.utcnow()

    def legal_clue(self, clue_word):
        """
        Checks if the clue provided by the spymaster is a legal clue

        @param clue_word (str): the clue word provided by the spymaster

        @returns bLegal [bool] : True if the clue is legal, False if illegal
        @returns explanation [str] : Why the clue was illegal ('Yes' if it was legal)
        """
        unguessed_words = self.gameboard.unguessed_words()

        # check if clue word >1 word:
        if " " in clue_word:
            return False, 'Illegal clue: contained space(s)'
        if "-" in clue_word:
            return False, 'Illegal clue: contained hyphen(s)'

        # Check partial words:
        for word in unguessed_words:
            if clue_word in word:
                return False, f'Illegal clue: clue_word in unguessed word {word}'
            if word in clue_word:
                return False, f'Illegal clue: unguessed word {word} in clue_word'

        # Check Lemmas
        lemmatizer = WordNetLemmatizer()
        illegal_lemmas = set()
        for word in unguessed_words:
            # The primary lemma may be different for different parts of speech. Check all possible parts of speech:
            for pos in ['n',  # noun
                        'v',  # verb
                        'a',  # adjective
                        's',  # adjective satellite
                        'r'  # adverb
                        ]:
                illegal_lemmas.add(lemmatizer.lemmatize(word, pos=pos))

        for pos in ['n',  # noun
                    'v',  # verb
                    'a',  # adjective
                    's',  # adjective satellite
                    'r'  # adverb
                    ]:
            lemma=lemmatizer.lemmatize(clue_word, pos=pos)
            if lemma in illegal_lemmas:
                # This is an illegal clue based on lemmas
                # Figure out which boardword it overlaps with so explanation can be given:
                for boardword in unguessed_words:
                    for pos in ['n',  # noun
                                'v',  # verb
                                'a',  # adjective
                                's',  # adjective satellite
                                'r'  # adverb
                                ]:
                        if lemmatizer.lemmatize(boardword, pos=pos) == lemma:
                            return False, f"Illegal clue: clue_word lemma '{lemma}' (POS={pos}) overlaps a lemma of " \
                                          f"boardword '{boardword}'"

        # If has not returned False by now, it has passed all the tests
        return True, 'Yes'

    def check_game_over(self, result):
        """
        Checks to see if one of the conditions has been met to end the game. If so, updates game_completed to True and
            populates game_result dict

        @param result (int): the team of the most recently tapped word. Used to check if the Assassin has been tapped
        """
        if result == -1:  # If the operative guessed the assassin word
            self.logger.add_event({'event': 'game over',
                                   'timestamp': datetime.utcnow(),
                                   'reason': f'Team {self.curr_team} guessed assassin word'
                                   })
            self.game_completed = True
            self.game_result['winning team'] = {'num' : self.not_curr_team}
            self.game_result['losing team'] = {'num' : self.curr_team}
        elif self.gameboard.remaining(self.curr_team) == 0: #if the current team has no words left to guess
            self.logger.add_event({'event': 'game over',
                                   'timestamp': datetime.utcnow(),
                                   'reason': f'All team {self.curr_team} words guessed'
                                   })
            self.game_completed = True
            self.game_result['winning team'] = {'num' : self.curr_team}
            self.game_result['losing team'] = {'num' : self.not_curr_team}
        elif self.gameboard.remaining(self.not_curr_team) == 0: #if the other (not-current) team has no words left to guess
            self.logger.add_event({'event': 'game over',
                                   'timestamp': datetime.utcnow(),
                                   'reason': f'All team {self.not_curr_team} words guessed'
                                   })
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
            self.game_result['end time'] = datetime.utcnow()
            self.game_result['final gameboard'] = self.gameboard

            self.update_ratings()

            for i, team in enumerate(self.teams):
                if i == self.game_result['winning team']['num']-1:
                    team_key = 'winning team'
                else:
                    team_key = 'losing team'

                for j, player in enumerate(team):
                    self.game_result[team_key]['players'][j]['Elo after update'] = deepcopy(player.Elo)
            self.log_end_of_game()

    def switch_teams(self):
        """
        Switches the active team
        """
        self.curr_team = self.not_curr_team

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
        Returns info about who the game is waiting on including:
        @returns wait_team [int] : <1 or 2>
        @returns wait_role [str] : <'spymaster' or 'operative'>
        @returns wait_player.player_id [int] : player_id of the player being waited on
        @returns waiting_for [str] : <'query' or 'input'>
        @returns wait_duration [timedelta] : the amount of time the game has been waiting for the next action
        """
        wait_team = self.curr_team
        wait_role = self.waiting_on
        if self.waiting_on == 'spymaster':
            wait_player = self.spymasters[self.curr_team-1]
        else:
            wait_player = self.operatives[self.curr_team - 1]
        if self.waiting_query_since > self.waiting_inputs_since:  # If waiting_query_since reset more recently than waiting_inputs_since
            waiting_for = 'query'
            wait_duration = datetime.utcnow() - self.waiting_query_since
        else:
            waiting_for = 'input'
            wait_duration = datetime.utcnow() - self.waiting_inputs_since
        return wait_team, wait_role, wait_player.player_id, waiting_for, wait_duration

    def is_players_turn(self, player_id):
        """
        Checks if it is the turn of player_id

        @param player_id : the player_id of the player to be checked
        @returns is_players_turn [bool] : True if the player_id that the game is waiting for matches the player_id
            supplied
        """
        if self.waiting_on == 'spymaster':
            waiting_on_player_id = self.spymasters[self.curr_team - 1].player_id
        else:
            waiting_on_player_id = self.operatives[self.curr_team - 1].player_id
        return player_id == waiting_on_player_id

    def check_timed_out(self, max_duration):
        """
        Checks if the player being waited on has timed out. If so, updates game_result dict accordingly.

        @param max_duration [timedelta] : the threshold for declaring a game timed out

        @returns game_timed_out [bool]: True if the game has timed out, False if not
        """
        wait_team, wait_role, wait_player, waiting_for, wait_duration = self.waiting_on_info()
        if wait_duration > max_duration:
            self.game_timed_out = True
            self.game_result = {'timed out waiting on': {'team': wait_team,
                                                         'role': wait_role,
                                                         'player_id': wait_player,
                                                         'waiting for': waiting_for,
                                                         'waiting duration': str(wait_duration)
                                                         },
                                'teams' : {'team 1' : [{'player_id' : player.player_id} for player in self.teams[0]],
                                           'team 2' : [{'player_id' : player.player_id} for player in self.teams[1]]
                                           },
                                'start time' : self.game_start_time,
                                'end time' : datetime.utcnow(),
                                'final gameboard' : self.gameboard
                                }
            self.log_end_of_game()
        return self.game_timed_out

    def log_end_of_game(self):
        """
        Adds elements from self.game_result to the game log. Called when either the game completes or times out.
        """
        self.logger.set_field('in_progress', False)
        for key, val in self.game_result.items():
            if key == 'final gameboard':  # cannot store gameboard object in mongoDB
                # instead, just store the boardmarkers array, converting it to mongo-storable types first
                self.logger.set_field('boardmarkers',[[float(x) for x in row] for row in self.gameboard.boardmarkers])
            else:
                self.logger.set_field(key, val)

class LocalLogger(object):
    """
    The default logger if no logger is provided when a game is instantiated.
    Records a log of all the actions taken in a game.
    When games are run on the server, this logger will not be used. A logger that links to the mongoDB will be used
        instead. See class MongoLogger in TWIML_codenames_API_Server

    Instance variables:
        .game_log [dict] : the game log. Static information for the game are stored as key,val pairs in the game_log
            dict. Events are stored in a list embedded within the game_log dict.

    Functions:
        .record_config(gameboard, teams) : called when a TWIML_codenames.game object is initialized. Populates starting
            info about the game to the game_log
        .set_field(field_name, val) : sets a field in the top level of the game_log
        .add_event(event_dict) : adds the event to the end of the list of events
    """
    def __init__(self):
        self.game_log = {'in_progress':True, 'events':[]}

    def record_config(self, gameboard, teams):
        """
        Called when a TWIML_codenames.game object is initialized. Populates starting
            info about the game to the game_log

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
        self.game_log[field_name] = val

    def add_event(self, event_dict):
        """
        Adds the event to the end of the list of events

        @param event_dict [dict] : the dictionary capturing the info associated with the event
        """
        self.game_log['events'].append(event_dict)

class Player(object):
    """
    An object containing all the info needed to track the player's performance

    Instance variables:
        .player_id [int] : this player's unique 4-digit identifier
        .Elo [dict] : a dictionary of form {'Spymaster': Elo rating, 'Operative': Elo rating} storing the Elo ratings of
            this player for both roles
        .record [dict] : a nested dictionary of form {'Spymaster': {'W': num_wins, 'L': num_losses},
                                                      'Operative': {'W': num_wins, 'L': num_losses}}
            storing the win and loss records of this player for both roles

    Properties:
        .Elo_combined [float] : the average of this player's Spymaster and Operative Elo ratings

    Functions:
        .update_ratings(role, result, own_team_avg_Elo, opp_team_avg_Elo) : Updates the win/loss record and Elo rating
            of the player
        .calc_delta_Elo(result, own_team_avg_Elo, opp_team_avg_Elo) : Calculates the change in Elo rating of the player
    """
    def __init__(self, player_id, Elo = {'Spymaster': 1500., 'Operative': 1500.},
                 record = {'Spymaster': {'W': 0, 'L': 0}, 'Operative': {'W': 0, 'L': 0}}):
        """
        By default, a new player object is created with Elo 1500 for both roles and W-L record of 0-0 for both roles.
        The option to provide the Elo and record are included so that the server can recreate a player object from info
            stored on disk.

        @param player_id [int] : the unique id for the current player
        @param Elo [dict](optional) : the dict storing the player's Elo ratings for both roles. Used when recreating a
            player object from disk
        @param record [dict](optional) : the dict storing the player's W-L records for both roles. Used when recreating
            a player object from disk
        """
        self.player_id = player_id
        self.Elo = Elo
        self.record = record

    @property
    def Elo_combined(self):
        """
        Returns the combined Elo for this player
        """
        return (self.Elo['Spymaster'] + self.Elo['Operative']) / 2

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
