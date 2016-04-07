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
        levels = list(mongo.user_levels.find().sort(
                    [("exp", pymongo.ASCENDING)]))
        if not levels:
            log.error("Please init UserLevels collection")
            return None
        redisdb.set("cache:userlevels", dumps(levels))
    for l in levels:
        if exp < l['exp']:
            l['_id'] = 'level{0}'.format(int(list(filter(str.isdigit, l['_id']))[0])-1)
            return l['_id']


def get_post_user(post_id):
    """get all users in post_id"""
    users = set(x['post_id'] for x in mongo['commens_%s' % post_id].find())
    return users


def add_exp(user, exp):
    """add exp to user 
    input:User instance"""
    user.exp = user.exp + exp
    new_level = get_level(user.exp)
    if new_level != user.user_level_id:
        user.user_level_id = new_level
        notification.level_up.delay(user._id, user.user_level_id)


def minus_exp(user, exp):
    """minus exp to user
    input:User instance"""
    user.exp = user.exp - exp
    new_level = get_level(user.exp)
    if new_level != user.user_level_id:
        user.user_level_id = new_level
        notification.level_down.delay(user._id, user.user_level_id)


def new_comment(post):
    """post have a new comment
    input:Post instance"""
    notification.new_reply.delay(post.author_id, post.post_id, post.comment_id)


def self_post_heart(post):
    """post have a new heart
    input:Post instance"""
    notification.new_heart.delay(post.author_id, post.post_id)


def max_punish(user):
    """frozen user
    input:User instance"""
    notification.frozen_user.delay(user._id)


def restrict_post(user, expire_time):
    """forbit user to post in expire_time, expire_time is in seconds
    input:User instance"""
    notification.forbid_post.delay(user._id, expire_time)


def update_system(user, version):
    """remind user to update software
    input:User instance"""
    notification.forbid_post.delay(user._id, version)

