"""
model_template.py: template for models to be used in the TWIMLfest 2020 codenames competition
Dan Hilgart <dhilgart@gmail.com>
see https://czechgames.com/files/rules/codenames-rules-en.pdf for game rules
"""
import TWIML_codenames
import numpy as np
import pickle

def generate_clue(team_num, gameboard):
    """
    This is the function that will be called when your bot is the Spymaster
    Your bot will need to provide a clue_word and a clue_count which will be used by your teammate's bot to guess words
    Make sure to provide a legal clue (see TWIML_codenames.py for how legality is assessed) or the turn will be skipped
    The following inputs will be provided:
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
    wordlist = pickle.load( open("wordlist.p", "rb" ) ) #load the wordlist from a pickled file in my directory
    clue_word = np.random.choice(wordlist) #pick a clue word at random from the wordlist
    clue_count = np.random.randint(3) + 1 #give a random clue_count of 1, 2, or 3
    ### END YOUR CODE
    
    return clue_word, clue_count

def generate_guesses(team_num, clue_word, clue_count, unguessed_words, boardwords, boardmarkers):
    """
    This is the function that will be called when your bot is the Operative
    Your teammate's bot will provide you with a clue_word and a clue_count. Use them to generate a list of words to
        guess.
    The following inputs will be provided:
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
    guesses = [x for x in np.random.choice(unguessed_words,np.random.randint(4))] #pick 0-3 words at random from the unguessed list
    ### END YOUR CODE
    
    return guesses
