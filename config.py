from pydantic import BaseSettings
import pymongo 

class Settings(BaseSettings):
    db_connection: str 
    db_collection:str = 'codenames'

    class Config:
        env_file = ".env"

def get_connection():
    settings = Settings()


    print (settings)
    db_client = pymongo.MongoClient(settings.db_connection)
    db = db_client[settings.db_collection]

    db.players.create_index([('player_id', pymongo.ASCENDING)], unique=True)
    db.games.create_index([('game_id', pymongo.ASCENDING)], unique=True)

    return db
