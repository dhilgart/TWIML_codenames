"""
my_model.py: template for models to be used in the TWIMLfest 2020 Codenames competition
Dan Hilgart <dhilgart@gmail.com> and Yuri Shlyakhter <yuri.shlyakhter@gmail.com>
see https://czechgames.com/files/rules/codenames-rules-en.pdf for game rules
"""
"""
------------------------------------------------------------------------------------------------------------------------
                                                    Required Imports
------------------------------------------------------------------------------------------------------------------------
Do not remove these
"""
import TWIML_codenames
import numpy as np

"""
------------------------------------------------------------------------------------------------------------------------
                                                      Your Imports                                                      
------------------------------------------------------------------------------------------------------------------------
Add/modify as necessary
"""
### YOUR CODE HERE
import spacy # after installing, be sure to run 'python -m spacy download en_core_web_lg'
import itertools
### END YOUR CODE

"""
------------------------------------------------------------------------------------------------------------------------
                                                  Your Global Variables
------------------------------------------------------------------------------------------------------------------------
Place anything here that you want to be loaded when this module is imported by TWIML_codenames_API_client.py 
For example, if you are loading word vectors, load them here as global variables so they do not have to be loaded each 
    time the generate_clue and generate_guesses functions are called  
"""
### YOUR CODE HERE
nlp = spacy.load("en_core_web_lg") # if OSError: [E050] Can't find model 'en_core_web_lg', run this from command line:
                                   # 'python -m spacy download en_core_web_lg'

clue_word_candidates = [word for word in
                        np.random.choice([line.strip() for line in open('nounlist.txt', 'r').readlines()],
                                         1000,replace=False) # number of candidate words reduced to improve runtime
                        ]
### END YOUR CODE

"""
------------------------------------------------------------------------------------------------------------------------
                                                     Your Functions                                                     
------------------------------------------------------------------------------------------------------------------------
Add/modify functions as necessary
"""
### YOUR CODE HERE
def dist(word1, word2):
    """
    Calculates the vector-distance between two words
    """
    tokens = nlp(word1 + " " + word2)
    return 1 - tokens[0].similarity(tokens[1])
### END YOUR CODE

"""
------------------------------------------------------------------------------------------------------------------------
                                                   Required Functions                                                   
------------------------------------------------------------------------------------------------------------------------
These are the two required functions that you must have in your model file.
"""
def generate_clue(game_id, team_num, gameboard: TWIML_codenames.Gameboard):
    """
    This is the function that will be called when your bot is the Spymaster
    Your bot will need to provide a clue_word and a clue_count which will be used by your teammate's bot to guess words
    Make sure to provide a legal clue (see TWIML_codenames.py for how legality is assessed) or the turn will be skipped
    The following inputs will be provided:
    @param game_id (int): the unique identifier for this game. Can be used to locally track info about this game as it 
        plays out
    @param team_num (int): 1 if you are on the first team, 2 if you are on the second team. This matches with the
        gameboard key
    @param gameboard (TWIML_codenames.Gameboard): an object containing the current state of the gameboard. Note that
        this is a copy of the gameboard so any changes made to it will not impact the true gameboard. See
        TWIML_codenames.py for the full details of the TWIML_codenames.Gameboard class. Some useful commands:
            gameboard.boardwords -- 5x5 np.array[str]: the 5x5 grid of words. Remains unchanged after initialization
            gameboard.boardkey -- 5x5 np.array[int]: the key that tells which words belong to which team. Remains
                unchanged after initialization. (1 = team 1, 2 = team 2, 0 = neutral, -1 = assassin)
            gameboard.boardmarkers -- 5x5 np.array[float]: the array that tracks which words have been tapped and what
                was revealed. Starts as an array of np.NaNs. As words are tapped (guessed), the values from the boardkey
                are added for each tapped word.
            gameboard.unguessed_words(team_num[int](optional)) -- list[str]: returns a list of unguessed words for the
                supplied team_num (1 = team 1, 2 = team 2, 0 = neutral, -1 = assassin). If no team_num is supplied, will
                return all remaining unguessed words.
            gameboard.remaining(team_num[int]) -- list[str]: Counts how many cards are left for the supplied team_num

    Please return the outputs as follows:
    @returns clue_word (str): the one-word clue that must not match any part of the remaining words on the board
    @returns clue_count (int): the count of how many board-words are related to the clue word. There are two special
        cases for the clue count:
            A Spymaster can give a clue count of 0 which communicates to the Operative that they should guess words that
                are NOT related to the clue word.
            A spymaster may also give a clue for infinity, allowing the Operative to make as many guesses as they like.
                To give a clue for infinity, provide an int of 10.
    """
    ### YOUR CODE HERE
    # Algorithm based on the following paper:
    # Cooperation and Codenames:Understanding Natural Language Processing via Codenames
    # by A. Kim, M. Ruzmaykin, A. Truong, and A. Summerville 2019
    threshold = 0.5

    unguessed_good_words = gameboard.unguessed_words(team_num)
    unguessed_bad_words = [word for word in gameboard.unguessed_words() if word not in unguessed_good_words]

    #filter out words that are on the board
    candidates=[word for word in clue_word_candidates if word not in gameboard.unguessed_words()]

    good_word_distances = {}
    for good_word in unguessed_good_words:
        good_word_distances[good_word] = {}
        for clue_candidate in candidates:
            good_word_distances[good_word][clue_candidate] = dist(good_word, clue_candidate)

    bad_word_distances = {}
    for bad_word in unguessed_bad_words:
        bad_word_distances[bad_word] = {}
        for clue_candidate in candidates:
            bad_word_distances[bad_word][clue_candidate] = dist(bad_word, clue_candidate)

    clue_count = 0
    clue_word = None
    d = float('Inf')

    for clue_count_to_try in range(len(unguessed_good_words)):
        for good_word_combo in itertools.combinations(unguessed_good_words,clue_count_to_try):
            for clue_candidate in candidates:
                w_d = float('Inf')
                for bad_word in unguessed_bad_words:
                    if bad_word_distances[bad_word][clue_candidate] < w_d:
                        w_d = bad_word_distances[bad_word][clue_candidate]
                    d_r = 0
                    for good_word in good_word_combo:
                        if good_word_distances[good_word][clue_candidate] > d_r:
                            d_r = good_word_distances[good_word][clue_candidate]
                        if d_r < d and d_r < w_d and d_r < threshold:
                            d = d_r
                            clue_word = clue_candidate
                            clue_count = clue_count_to_try
    ### END YOUR CODE
    
    return clue_word, clue_count

def generate_guesses(game_id, team_num, clue_word, clue_count, unguessed_words, boardwords, boardmarkers):
    """
    This is the function that will be called when your bot is the Operative
    Your teammate's bot will provide you with a clue_word and a clue_count. Use them to generate a list of words to
        guess.
    The following inputs will be provided:
    @param game_id (int): the unique identifier for this game. Can be used to locally track info about this game as it 
        plays out
    @param team_num (int): 1 if you are on the first team, 2 if you are on the second team. This matches with the
        boardmarkers array
    @param clue_word (str): the one-word clue from your spymaster
    @param clue_count (int): the count of how many board-words are related to the clue word. There are two special
        cases for the clue count:
            A Spymaster can give a clue count of 0 which communicates to the Operative that they should guess words that
                are NOT related to the clue word.
            A spymaster may also give a clue for infinity, allowing the Operative to make as many guesses as they like.
                An int of 10 is used to represent a clue for infinity.
    @param unguessed_words (list[str]): a 1-d list of all the remaining words that have not yet been tapped
    @param boardwords (5x5 np.array[str]): the 5x5 grid of words. Remains unchanged after initialization
    @param boardmarkers (5x5 np.array[float]): the array that tracks which words have been tapped and what was revealed.
        Starts as an array of np.NaNs. As words are tapped (guessed), the team number (1 = team 1, 2 = team 2,
        0 = neutral, -1 = assassin) of each tapped word are added.

    Please return the outputs as follows:
    @returns guesses (list[str]): a list of the words that you would like to tap in the order you want them tapped.
        Words on the list will continue to be tapped until a word is tapped that is not one of your team's words
    """
    ### YOUR CODE HERE
    # Algorithm based on the following paper:
    # Cooperation and Codenames:Understanding Natural Language Processing via Codenames
    # by A. Kim, M. Ruzmaykin, A. Truong, and A. Summerville 2019
    threshold_for_guessing = 0.2

    guesses = []
    while len(guesses) < clue_count:
        best = None
        d = float('Inf')
        for word in unguessed_words:
            distance = dist(clue_word, word)
            if (distance < d):
                d = distance
                best = word
        if (best and d < threshold_for_guessing):
            guesses.append(best)
            unguessed_words.remove(best)
        else:
            break
    ### END YOUR CODE
    
    return guesses
