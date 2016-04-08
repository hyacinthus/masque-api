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


def add_exp(user, exp):
    """add exp to user 
    input:User instance"""
    user.exp = user.exp + exp
    new_level = get_level(user.exp)
    if new_level != user.user_level_id:
        user.user_level_id = new_level
        notification.level_up.delay(str(user._id), user.user_level_id)


def minus_exp(user, exp):
    """minus exp to user
    input:User instance"""
    user.exp = user.exp - exp
    new_level = get_level(user.exp)
    if new_level != user.user_level_id:
        user.user_level_id = new_level
        notification.level_down.delay(str(user._id), user.user_level_id)


def new_remark(comment):
    """post have a new comment
    input:Comment instance"""
    user_stars = list(mongo.user_stars.find({'post_id': comment.post_id}))
    user_comments = list(mongo.user_comments.find({'post_id': comment.post_id}))
    notification.new_reply.delay(comment.author, comment.post_id, str(comment._id))
    for star in user_stars:
        notification.star_new_reply.deplay(star['user_id'], star['theme_id'],
                                           star['post_id'], str(comment._id))
    for element in user_comments:
        notification.comment_new_reply.deplay(element['user_id'], element['theme_id'],
                                              element['post_id'], str(comment._id))


def post_heart(post):
    """post have a new heart
    input:Post instance"""
    notification.new_heart.delay(post.author, str(post._id))


def max_punish(user):
    """frozen user
    input:User instance"""
    notification.frozen_user.delay(str(user._id))


def restrict_post(user, expire_time):
    """forbit user to post in expire_time, expire_time is in seconds
    input:User instance"""
    notification.forbid_post.delay(str(user._id), expire_time)


def update_system(user, version):
    """remind user to update software
    input:User instance"""
    notification.forbid_post.delay(str(user._id), version)


class dict2obj(object):
    """convert dict to object"""
    def __init__(self, dic):
        for k, v in dic.items():
            if isinstance(v, (tuple, list)):
                self.__setattr__(k, [dict2obj(i) if isinstance(i, dict) else i for i in v])
            else:
                self.__setattr__(k, dict2obj(v) if isinstance(v, dict) else v)
