from pydantic import BaseSettings
import pymongo 
import mongoengine 

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

    db.user.create_index([('user_name', pymongo.ASCENDING)],
                                  unique=True)

    return db
