# TWIML_codenames
This repo contains the code for running the TWIMLfest codenames competition

## Competition Overview

Bring your AI to a [Codenames](https://en.wikipedia.org/wiki/Codenames_(board_game)) competition! Every contestant will submit an AI-powered bot. Bots will need to be able to both give 1-word clues and interpret their teammate-bot's clues. Contestants' bots will be randomly paired up and compete against another team of bots. Games will be simulated according to the regular [rules of Codenames](https://czechgames.com/files/rules/codenames-rules-en.pdf) to determine which bot is best! Will the winner take a word embeddings approach? A reinforcement learning approach? Something off the wall?

The competition will take place via a central server that hosts all the games. Anytime that the server is open, you can launch your bot to play games. Your bot will be paired up at random with another active bot logged into the server to form a team. Each time there are enough active players a new game will start. Upon completion of each game, the winners’ ratings will increase and the losers’ ratings will decrease using an Elo rating system. Then your bot will be returned to the pool of available bots to await being paired with another random partner. 

The competition server will be open for practice for the first week. Then ratings will reset, and the final competition will take place the second week. At the end of the competition, the final Elo ratings will be used to determine the winners. 

A python template is provided for your bot containing two functions that you will need to populate: generate_clue() and generate_guesses(). Generate_clue is used when you are the spymaster (the one giving the clues). This function will need to return a one-word clue and a count of how many words on the board are tied to that clue. Generate_guesses is used when you are the operative (the one making the guesses) and will need to return a list of words-on-the-board that you want to guess in the order you want to guess them. These two functions are the only code you need to create to enter. 

You will be provided with my_model.py (the python template for your model), a client_run.py file that takes care of all of the API interactions with the server and calls the generate_clue() and generate_guesses() functions at the appropriate times, and (for reference) all of the code that is used to run the games. In order to play games, all you will need to do is run “python client_run.py” from your command line while the server is open. It will take care of the rest!

## Competition Dates (2020)

Practice server open October 14-21

Final competition server open October 21-28

Check-ins Wednesdays at 2PM PT: 

- Oct 14th Kickoff, overview of the competition, optional play human Codenames with others afterward
- Oct 21st Collaboration and troubleshooting
- Oct 28th Debrief and awards

## Competitor Instructions

You will need the following files:

##### Modify these files:

- myPlayerID-Key.txt - populate your player_ID and player_key here (these will be emailed to you upon confirmation of your sign-up)
- my_model.py - this is where your code goes

##### Do NOT modify these files:

- TWIML_codenames.py - defines the classes used for the competition. Imported by my_model.py
- client_run.py - this automates all the interactions with the server, calling the two functions from my_model.py when needed
- TWIML_codenames_API_Client.py - helper functions for client_run.py
- requirements.txt - defines the minimum libraries you will need

#### Important Notes 

You are responsible for your own compute. You may run your client on local hardware or on cloud compute. Either way, whenever you want to join games, simply run the following command: "python client_run.py". The file will take care of the rest. 

Your algorithm must return a response in less than 5 minutes or the server will consider your bot timed out and will end the game early.

## Other files in Repo

- server_run.py - runs the server; processes requests from clients as they come in
- TWIML_codenames_API_Server.py - helper functions and classes for server_run.py
- Dockerfile - defines the docker container that runs the API server
- TWIML_codenames Demo.ipynb - a jupyter notebook demonstrating the functionality of the TWIML_codenames.py classes
- README.md - this file



## Developers' references

To do list located here: [https://docs.google.com/document/d/1_G3r4u9DZM-hZfyl0TG8nQ2S7U5jiX5c6awG-cKuXDo/edit](https://docs.google.com/document/d/1_G3r4u9DZM-hZfyl0TG8nQ2S7U5jiX5c6awG-cKuXDo/edit)