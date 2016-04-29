import logging

from bson.objectid import ObjectId

from config import MongoConfig, RedisConfig
from model import connection, redisdb
from tasks import app
from tools import detection
from tools.oss import OssConnection

oc = OssConnection()
log = logging.getLogger("masque.task.notifications")
expire = RedisConfig.NOTIFI_EXPIRE * 3600


def save2redis(notifi):
    # 通知暂存到 Redis
    redisdb.lpush("user:{}:notifications".format(notifi.user_id), notifi._id)
    hmap = notifi.copy()
    hkey = "notification:{}".format(notifi._id)
    redisdb.hmset(hkey, hmap)
    redisdb.expire(hkey, expire)  # 设置提醒过期时间
    log.info("Hash key %s has been saved in redis" % hkey)


@app.task
def new_reply(author_id, theme_id, post_id, comment_id):
    collection = connection[MongoConfig.DB]["posts_" + theme_id]
    cursor = collection.Posts.find_one({"_id": ObjectId(post_id)})
    notifi_user = connection.Users.find_one({"_id": ObjectId(cursor.author)})
    if notifi_user.options.new_comment:
        # 只有用户允许通知才会提醒
        content = "Your post %s have a new comment %s" % (post_id, comment_id)
        log.info(content)
        notifi = connection.Notifications()
        notifi.title = "您的帖子有新评论啦"
        notifi.type = "comment"
        notifi.theme_id = theme_id
        notifi.post_id = post_id
        notifi.user_id = author_id
        notifi.comment_id = comment_id
        notifi.content = content
        notifi.save()
        save2redis(notifi)


@app.task
def star_new_reply(author_id, theme_id, post_id, comment_id):
    notifi_user = connection.Users.find_one({"_id": ObjectId(author_id)})
    if notifi_user.options.star_comment:
        # 只有用户允许通知才会提醒
        content = "There are new comments %s for the post %s you viewed" % (
            post_id, comment_id)
        log.info(content)
        notifi = connection.Notifications()
        notifi.type = "comment"
        notifi.theme_id = theme_id
        notifi.post_id = post_id
        notifi.comment_id = comment_id
        notifi.user_id = author_id
        notifi.content = content
        notifi.save()
        save2redis(notifi)


@app.task
def comment_new_reply(author_id, theme_id, post_id, comment_id):
    content = "There are new comments %s for the post %s you remarked" % (
        comment_id, post_id)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "comment"
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.user_id = author_id
    notifi.content = content
    notifi.save()


@app.task
def new_heart(author_id, theme_id, post_id):
    notifi_user = connection.Users.find_one({"_id": ObjectId(author_id)})
    if notifi_user.options.post_hearted:
        # 只有用户设置提醒才会有效
        content = "Your post %s have a new heart" % post_id
        log.info(content)
        notifi = connection.Notifications()
        notifi.type = "message"
        notifi.user_id = author_id
        notifi.theme_id = theme_id
        notifi.post_id = post_id
        notifi.content = content
        notifi.save()
        save2redis(notifi)


@app.task
def comment_new_heart(user_id, theme_id, post_id, comment_id):
    notifi_user = connection.Users.find_one({"_id": ObjectId(user_id)})
    if notifi_user.options.comment_hearted:
        content = "There are new hearts for the comment %s you remarked" % comment_id
        log.info(content)
        notifi = connection.Notifications()
        notifi.type = "message"
        notifi.user_id = user_id
        notifi.theme_id = theme_id
        notifi.post_id = post_id
        notifi.content = content
        notifi.save()
        save2redis(notifi)


@app.task
def level_up(user_id, user_level):
    content = "Level up! your new level is %s" % user_level
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "levelup"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()
    save2redis(notifi)


@app.task
def level_down(user_id, user_level):
    content = "Level down! your new level is %s" % user_level
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def encourage_valid_feedback(user_id, exp, name):
    content = "Thanks, your feedback %s have solved, exp +%s" % (name, exp)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "encourage"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def publish_forbid_post(user_id, expiry=7 * 24 * 3600):
    content = "Warning! you are prohibited to post %s" % expiry
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def publish_invalid_report_post(author_id, theme_id, post_id, exp):
    content = "you give us a invalid report %s, exp %s" % (post_id, exp)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = author_id
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.content = content
    notifi.save()


@app.task
def publish_invalid_report_comment(author_id, theme_id, comment_id, exp):
    content = "you give us a invalid report %s, exp %s" % (comment_id, exp)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = author_id
    notifi.theme_id = theme_id
    notifi.post_id = comment_id
    notifi.content = content
    notifi.save()


@app.task
def publish_illegal_post(user_id, theme_id, post_id):
    content = "you post a illegal post %s" % post_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.content = content
    notifi.save()


@app.task
def publish_illegal_comment(user_id, theme_id, post_id, comment_id):
    content = "you post a illegal comment %s" % comment_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.comment_id = comment_id
    notifi.content = content
    notifi.save()


@app.task
def publish_illegal_comment(user_id, theme_id, post_id, comment_id):
    content = "you post a illegal comment %s" % comment_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.comment_id = comment_id
    notifi.content = content
    notifi.save()


@app.task
def frozen_user(user_id):
    content = "Warning! your account has been frozen "
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def exp_up(user_id, user_exp):
    content = "Congratulation! your exp up to %s " % user_exp
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "encourage"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def update_system(user_id, version):
    content = "Great news, you have a new version %s can be updated" % version
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "message"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def check_image(bucket, image_id, author):
    content = "check image: %s/%s" % (bucket, image_id)
    img_url = oc.bucket.sign_url("GET", bucket + '/' + image_id, 60)
    label, rate = detection.detect(img_url)
    if label:
        detect = connection.Detections()
        detect._id = image_id
        detect.author = author
        detect.bucket = bucket
        detect.save()
        log.info(content)
        notifi = connection.Notifications()
        notifi.type = "message"
        notifi.user_id = author
        notifi.content = content
        notifi.save()


@app.task
def bind_cellphone(user_id, cellphone):
    content = "you have binded cellphone %s" % cellphone
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "message"
    notifi.content = content
    notifi.user_id = user_id
    notifi.save()


@app.task
def publish_porn_image(user_id, image_id):
    content = "you post a illegal porn image %s" % image_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "publish"
    notifi.content = content
    notifi.user_id = user_id
    notifi.save()
