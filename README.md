# TWIML_codenames
This repo contains the code for running the [TWIMLfest](https://twimlai.com/twimlfest/) [codenames competition](https://twimlai.com/twimlfest/sessions/codenames-bot-competition/) based on the game ["Codenames" by Vlaada Chvátil](https://czechgames.com/en/codenames/).

## Competition Overview

Bring your AI to a Codenames [[wiki](https://en.wikipedia.org/wiki/Codenames_(board_game))] [[video explanation of rules](https://www.youtube.com/watch?v=C97mCg9AxZc)] competition! Every contestant will build an AI-powered bot. Bots will need to be able to both give 1-word clues and interpret their teammate-bot's clues. Contestants' bots will be randomly paired up and compete against another team of bots. Games will be simulated according to the regular [rules of Codenames](https://czechgames.com/files/rules/codenames-rules-en.pdf) to determine which bot is best! Will the winner take a word embeddings approach? A reinforcement learning approach? Something off the wall?

The competition will take place via a central server that hosts all the games. Anytime that the server is open, you can launch your bot to play games. Your bot will be paired up at random with another active bot logged into the server to form a team. Each time there are enough active players a new game will start. Upon completion of each game, the winners’ ratings will increase and the losers’ ratings will decrease using an Elo rating system. Then your bot will be returned to the pool of available bots to await being paired with another random partner. 

The competition server will be open for practice for the first week. Then ratings will reset, and the final competition will take place the second week. At the end of the competition, the final Elo ratings will be used to determine the winners. 

A python template is provided for your bot containing two functions that you will need to populate: generate_clue() and generate_guesses(). Generate_clue is used when you are the spymaster (the one giving the clues). This function will need to return a one-word clue and a count of how many words on the board are tied to that clue. Generate_guesses is used when you are the operative (the one making the guesses) and will need to return a list of words-on-the-board that you want to guess in the order you want to guess them. These two functions are the only code you need to create to enter. 

You will be provided with my_model.py (the python template for your model), a client_run.py file that takes care of all of the API interactions with the server and calls the generate_clue() and generate_guesses() functions at the appropriate times, and (for reference) all of the code that is used to run the games.

Note: if you wish to focus on only one of the two roles, you will still need a functioning bot for the other role: in this case please leave the template bot as is for the other role.

## Prizes

In order to be eligible for prizes, you must consent to the terms and conditions: https://twimlai.com/contests/

Yes, there are prizes! Prizes can be distributed as a gift card/credit to your favorite cloud provider or as a credit for TWIML swag. No cash prizes will be distributed.

Prizes will be awarded based on highest Elo rating. Elo rating will be tracked separately for the Spymaster (generate_clues) and Operative (generate_guesses) roles and prizes will be awarded for the top 3 bots in each category. The main prize is for the best combined (average of the Spymaster and Operative) Elo ratings. Your entry may win up to one prize in each of the three categories. Prize amounts are:

|           | Combined | Spymaster | Operative |
| --------- | -------- | --------- | --------- |
| 1st Place | $ 125    | $ 50      | $ 50      |
| 2nd Place | $ 50     | $ 25      | $ 25      |
| 3rd Place | $ 25     | $ 10      | $ 10      |

## Rules

Unlike the official Codenames rules, we will not allow a multi-word clue even if it is a proper noun. All clues must be a single word without hyphens. Single word proper nouns *are* allowed.

This competition is meant to test the abilities of your bots. Please do not include any human interactions in your code (e.g. your bot waiting for you to pick the best of the options it generates or you just generating the codeword manually).

Competitors should not "team-up" to gain advantage. Any collaboration should be made in the [Slack channel](https://twimlai.slack.com/archives/C01CM9B3XL4) where anyone else can view and participate. 

In order to be eligible for prizes, your bot will need to have played a minimum of 100 games

## Competition Dates (2020)

Practice server open October 14-21

Final competition server open October 21-28

Check-ins Wednesdays at 2PM PT: 

- Oct 14th Kickoff, overview of the competition, optional play human Codenames with others afterward
- Oct 21st Collaboration and troubleshooting
- Oct 28th Debrief and awards

## Competitor Instructions

You will need the following 6 files from the repo:

##### Must modify these files:

- myPlayerID-Key.txt - populate your player_ID and player_key here (these will be emailed to you upon confirmation of your sign-up)
- my_model.py - this is where your code goes

##### Copy these files; modify at your own risk:

(You shouldn't need to modify these files. If you wish to do so, you may, though no support will be offered.)

- TWIML_codenames.py - defines the classes used for the competition. Imported by my_model.py
- client_run.py - this automates all the interactions with the server, calling the two functions from my_model.py when needed
- TWIML_codenames_API_Client.py - helper functions for client_run.py
- requirements.txt - defines the minimum libraries you will need

Detailed documentation for what each file/class/function/variable is used for is included within the files. Please place any questions about the code in the [Slack channel](https://twimlai.slack.com/archives/C01CM9B3XL4) or email to dhilgart@gmail.com.

When you are ready to compete, run the following from your command line:

```
python client_run.py
```

#### Important Notes 

You are responsible for your own compute. You may run your client on local hardware or on cloud compute. Either way, whenever you want to join games, simply run the following command: "python client_run.py". The file will take care of the rest. 

Your algorithm must return a response in less than 5 minutes or the server will consider your bot timed out and will end the game early.

##### Other API Endpoints:

There are other API endpoints available from the server which may provide some information that will be helpful to your bot. See server_run.py for full details. These include:

- @app.get("/{game_id}/log/")
  - returns the log for any game in binary (a.k.a. pickled) format
  - path parameters = game_id: the 6-digit unique identifier for this game
  - query parameters = player_id, player_key
- @app.get("/{player_to_pull}/games/")
  - returns a list of all the game_ids that a single player has been involved in
  - path parameters = player_to_pull: the player_id of the player whose games will be pulled
  - query parameters = None
- @app.get("/completed_games/")
  - returns a list of the game_ids of all completed games
  - Path, query parameters = None
- @app.get("/num_active_clients/")
  - returns a count of the number of clients currently active on the server
  - Path, query parameters = None

## Other files in Repo

- server_run.py - runs the server; processes requests from clients as they come in
- TWIML_codenames_API_Server.py - helper functions and classes for server_run.py
- config.py - configuration file used by the server for connection to the MongoDB
- Dockerfile - defines the docker container that runs the API server
- TWIML_codenames Demo.ipynb - a jupyter notebook demonstrating the functionality of the TWIML_codenames.py classes
- README.md - this file
- LICENSE - the license for this code: Mozilla Public License 2.0

