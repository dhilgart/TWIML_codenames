from pydantic import BaseModel
from typing import Optional

class UserStats(BaseModel):
    user_name: str
    score:Optional[int]  = None
    num_games:Optional[int]  = None

