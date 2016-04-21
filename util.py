import logging
import random

from bson.json_util import loads, dumps
from bson.objectid import ObjectId

from model import connection
from model import redisdb
from tasks import notification

log = logging.getLogger("masque.util")


def get_level(exp):
    """get the right level_id by exp"""
    if exp == 0:
        return "level0"
    levels_json = redisdb.get("cache:userlevels")
    if levels_json:
        levels = loads(levels_json)
    else:
        # 从小到大取出各等级边界值
        # (0, 20, 50, 200, 500, 1000, 2000, 5000, 10000, 20000, 40000)
        lst = tuple(
            i.exp for i in connection.UserLevels.find(sort=[("exp", 1)]))
        if not lst:
            log.error("Please init UserLevels collection")
        # 生成各等级经验取值范围列表
        # ((1, 20), (20, 50), (50, 200), (200, 500), (500, 1000), (1000, 2000),
        # (2000, 5000), (5000, 10000), (10000, 20000), (20000, 40000))
        levels = tuple(
            ((lambda i: i + 1 if i == 0 else i)(i), lst[lst.index(i) + 1])
            for i in lst if lst.index(i) + 1 < len(lst))
        redisdb.set("cache:userlevels", dumps(levels))
    for i in levels:
        if i[0] <= exp < i[1]:
            # 计算等级区间, 前闭后开
            level = "level%s" % (levels.index(i) + 1)
            break
    return level


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
    input:  User instance
            Comment instance
    """
    # 发的帖子有新评论
    cursor = connection.UserComments.find_one({"comment_id": comment._id})
    notification.new_reply.delay(comment.author, cursor.theme_id,
                                 comment.post_id, comment._id)
    # 关注的帖子有新评论
    user_stars = list(
        connection.UserStars.find({'post_id': comment.post_id}))
    for star in user_stars:
        notification.star_new_reply.delay(
            star['user_id'], star['theme_id'], star['post_id'], comment._id)


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
    for user in report.reporters:
        user = connection.Users.find_one({"_id": ObjectId(user)})
        add_exp(user, exp)
        if hasattr(report, 'post_id'):
            notification.publish_invalid_report_post.delay(report.reporters,
                                                           report.theme_id,
                                                           report.post_id, exp)
        else:
            notification.publish_invalid_report_comment.delay(report.reporters,
                                                              report.theme_id,
                                                              report.comment_id, exp)


def illegal_post(post):
    """remind user not to post illegal content
    input:Report Post instance"""
    cursor = connection.UserPosts.find_one({"post_id": post._id})
    notification.publish_illegal_post.delay(post.author, cursor.theme_id, post._id)


def illegal_comment(comment):
    """remind user not to post illegal content
    input:Report Comment instance"""
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


def check_image(user_image):
    """check image
    input: User Image instance"""
    notification.check_image.delay(user_image.category,
                                    user_image._id, user_image.author)


def porn_image(user_image, exp=-10):
    """remind user not to post porn_image
    input: User Image instance"""
    user = connection.Users.find_one({"_id": ObjectId(user_image.author)})
    add_exp(user, exp)
    notification.publish_porn_image.delay(user_image.author, user_image._id)
