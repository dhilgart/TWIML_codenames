from fastapi import APIRouter
import config
import pymongo 
import models
import logging


router = APIRouter()


db = config.get_connection()


@router.get("/{user_name}")
async def get(user_name:str):
    document = db['user'].find_one({'user_name': user_name})

    user = None
    if document:
        user = models.UserStats(**document)
    return user



@router.post("/")
async def update(user_stats:models.UserStats):
    #user = UserStats(user_name=user_name, score=score, num_games=num_games)
        

    filer = {'user_name': user_stats.user_name}
    res:pymongo.results.UpdateResult = db['user'].replace_one(filer ,user_stats.dict() , upsert= True)
    
    logging.debug(f"Updated {user_stats.user_name} with {user_stats}")
    return res.acknowledged

