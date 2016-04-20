import logging
import random

import pymongo
from bson.json_util import loads, dumps
from bson.objectid import ObjectId

from config import MongoConfig
from model import connection
from model import get_host, redisdb
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


def add_exp(user, exp=None):
    """add exp to user 
    input:User instance
    调用后必须save()保存经验变更到数据库
    """
    if not exp:
        # 默认经验值是1-5的随机数
        exp = random.sample([i for i in range(1, 6)], 1)[0]
    user.exp = user.exp + exp
    new_level = get_level(user.exp)
    if new_level != user.user_level_id:
        user.user_level_id = new_level
        if exp > 0:
            notification.level_up.delay(user._id, user.user_level_id)
        else:
            notification.level_down.delay(user._id, user.user_level_id)


def new_remark(comment):
    """post have a new comment
    input:Comment instance"""
    user_stars = list(mongo.user_stars.find({'post_id': comment.post_id}))
    cursor = connection.UserComments.find_one({"comment_id": comment._id})
    notification.new_reply.delay(comment.author, cursor.theme_id,
                                 comment.post_id, comment._id)
    for star in user_stars:
        notification.star_new_reply.deplay(star['user_id'], star['theme_id'],
                                           star['post_id'], comment._id)


def post_heart(post):
    """post have a new heart
    input:Post instance"""
    cursor = connection.UserPosts.find_one({"post_id": post._id})
    notification.new_heart.delay(post.author, cursor.theme_id, post._id)


def comment_heart(comment):
    """comment have a new heart
    input: Comment instance"""
    cursor = connection.UserComments.find_one({"comment_id": comment._id})
    notification.comment_new_heart.delay(comment.author, cursor.theme_id,
                                         comment.post_id, comment._id)


def valid_feedback(feedback, exp=10):
    """encourage user to feedback the problems of school_name
    input:Feedback instance"""
    user = connection.Users.find_one({"_id": ObjectId(feedback.author)})
    add_exp(user, exp)
    notification.encourage_valid_feedback.delay(feedback.author, exp, feedback.name)


def invalid_report(report, exp=-1):
    """remind user not to give invalid report
    input:Report instance"""
    user = connection.Users.find_one({"_id": ObjectId(report.author)})
    add_exp(user, exp)
    notification.publish_invalid_report.delay(report.author, report.theme_id,
                                              report.post_id, exp)


def illegal_post(post):
    """remind user not to post illegal content
    input:Post instance"""
    cursor = connection.UserPosts.find_one({"post_id": post._id})
    notification.publish_illegal_post.delay(post.author, cursor.theme_id, post._id)


def illegal_comment(comment):
    """remind user not to post illegal content
    input:Comment instance"""
    cursor = connection.UserComments.find_one({"comment_id": comment._id})
    notification.publish_illegal_comment.delay(comment.author, cursor.theme_id,
                                               comment.post_id, comment._id)


def frozen_user(user):
    """frozen user
    input:User instance"""
    notification.frozen_user.delay(user._id)


def bind_cellphone(user):
    """bind cellphone
    input:User instance"""
    add_exp(user, exp=20)
    notification.bind_cellphone.delay(user._id, user.cellphone)


def update_system(user, version):
    """remind user to update software
    input:User instance"""
    notification.update_system.delay(user._id, version)


def check_image(bucket, id):
    """check image
    input: bucket and id"""
    notification.check_image.delay(bucket, id)
