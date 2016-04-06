import logging
from bson.json_util import loads,dumps

import pymongo

from model import get_host, redisdb
from config import MongoConfig
from tasks import notification


log = logging.getLogger("masque.util")
mongo = pymongo.MongoClient(get_host())[MongoConfig.DB]


def get_level(exp):
    """get the right level_id by exp"""
    levels_json = redisdb.get("cache:userlevels")
    if levels_json:
        levels = loads(levels_json)
    else:
        levels = list(mongo.userlevels.find().sort(
                    [("exp", pymongo.ASCENDING)]))
        if not levels:
            log.error("Please init UserLevels collection")
            return None
        redisdb.set("cache:userlevels", dumps(levels))
    for l in levels:
        if exp > l['exp']:
            return l['_id']


def add_exp(user, exp):
    """add exp to user 
    input:User instance"""
    user.exp = user.exp + exp
    new_level = get_level(user.exp)
    if new_level != user.user_level_id:
        user.user_level_id = new_level
        notification.level_up.delay(user._id, user.user_level_id)

