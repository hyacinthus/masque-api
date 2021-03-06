import logging
from json import loads

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
def new_reply(dump_doc):
    # 发的帖子被评论
    doc = loads(dump_doc)
    collection = connection[MongoConfig.DB]["posts_" + doc["theme_id"]]
    cursor = collection.Posts.find_one({"_id": ObjectId(doc["post_id"])})
    notifi_user = connection.Users.find_one({"_id": ObjectId(cursor.author)})
    if notifi_user.options.new_comment:
        # 只有用户允许通知才会提醒
        log.info("post %s have a new comment %s" % (doc["post_id"], doc["_id"]))
        notifi = connection.Notifications()
        notifi.title = "您的帖子有新评论啦"
        notifi.type = "comment"
        notifi.theme_id = doc["theme_id"]
        notifi.post_id = doc["post_id"]
        notifi.user_id = doc["author"]
        notifi.comment_id = doc["_id"]
        notifi.content = doc["content"]
        notifi.mask_id = doc["mask_id"]
        notifi.index = doc["index"]
        notifi.save()
        save2redis(notifi)


@app.task
def star_new_reply(dump_doc):
    # 关注的帖子被评论
    doc = loads(dump_doc)
    user_stars = list(
        connection.UserStars.find({'post_id': doc["post_id"]}))
    for star in user_stars:
        notifi_user = connection.Users.find_one(
            {"_id": ObjectId(star['user_id'])}
        )
        if notifi_user._id != doc['current_user'] and notifi_user.options.star_comment:
            # 只有用户允许, 且回复者不是关注者本人才通知才会提醒
            log.info("There are new comments %s for the post %s you marked" % (
                doc["_id"], doc["post_id"]))
            notifi = connection.Notifications()
            notifi.title = "您关注的帖子有新评论啦"
            notifi.type = "comment"
            notifi.theme_id = doc['theme_id']
            notifi.post_id = star['post_id']
            notifi.comment_id = doc["_id"]
            notifi.user_id = star['user_id']
            notifi.content = doc["content"]
            notifi.mask_id = doc["mask_id"]
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
def new_heart(dump_doc):
    # 帖子收到新的感谢
    doc = loads(dump_doc)
    notifi_user = connection.Users.find_one({"_id": ObjectId(doc["author"])})
    if notifi_user.options.post_hearted:
        # 只有用户设置提醒才会有效
        log.info("Your post %s have a new heart" % doc["_id"])
        notifi = connection.Notifications()
        notifi.title = "您的帖子收到一个新的感谢"
        notifi.type = "heart"
        notifi.user_id = doc["author"]
        notifi.theme_id = doc["theme_id"]
        notifi.post_id = doc["_id"]
        notifi.content = doc["content"]
        notifi.mask_id = doc["mask_id"]
        notifi.save()
        save2redis(notifi)


@app.task
def comment_new_heart(dump_doc):
    # 评论收到新的感谢
    doc = loads(dump_doc)
    notifi_user = connection.Users.find_one({"_id": ObjectId(doc["author"])})
    if notifi_user.options.comment_hearted:
        log.info(
            "There are new hearts for the comment %s you remarked" % doc["_id"])
        notifi = connection.Notifications()
        notifi.title = "您的评论收到一个新的感谢"
        notifi.type = "heart"
        notifi.user_id = doc["author"]
        notifi.theme_id = doc["theme_id"]
        notifi.post_id = doc["post_id"]
        notifi.content = doc["content"]
        notifi.mask_id = doc["mask_id"]
        notifi.save()
        save2redis(notifi)


@app.task
def level_up(user_id, user_level):
    log.info("Level up! user %s new level is %s" % (user_id, user_level))
    notifi = connection.Notifications()
    notifi.type = "user"
    notifi.user_id = user_id
    notifi.title = "您升到了%s级" % user_level
    notifi.content = "加油!"
    notifi.save()
    save2redis(notifi)


@app.task
def level_down(user_id, user_level):
    log.info("Level down! user %s new level is %s" % (user_id, user_level))
    notifi = connection.Notifications()
    notifi.type = "user"
    notifi.user_id = user_id
    notifi.title = "您的等级掉到了%s级" % user_level
    notifi.content = "加油!"
    notifi.save()


@app.task
def encourage_valid_feedback(user_id, exp, name):
    content = "Thanks, your feedback %s have solved, exp +%s" % (name, exp)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def publish_forbid_post(user_id, expiry=7 * 24 * 3600):
    content = "Warning! you are prohibited to post %s" % expiry
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def publish_invalid_report_post(author_id, theme_id, post_id, exp):
    content = "you give us a invalid report %s, exp %s" % (post_id, exp)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
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
    notifi.type = "system"
    notifi.user_id = author_id
    notifi.theme_id = theme_id
    notifi.post_id = comment_id
    notifi.content = content
    notifi.save()


@app.task
def valid_report_post(author_id, theme_id, post_id, exp):
    content = "you give us a valid report %s, exp %s" % (post_id, exp)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = author_id
    notifi.title = "举报有效,获得颜值奖励%s" % exp
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.content = content
    notifi.save()
    save2redis(notifi)


@app.task
def valid_report_comment(author_id, theme_id, comment_id, exp):
    content = "you give us a valid report %s, exp %s" % (comment_id, exp)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = author_id
    notifi.title = "举报有效,获得颜值奖励%s" % exp
    notifi.theme_id = theme_id
    notifi.post_id = comment_id
    notifi.content = content
    notifi.save()
    save2redis(notifi)


@app.task
def publish_illegal_post(user_id, theme_id, post_id):
    content = "you post a illegal post %s" % post_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = user_id
    notifi.title = "您发了违规帖子"
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.content = content
    notifi.save()
    save2redis(notifi)


@app.task
def publish_illegal_comment(user_id, theme_id, post_id, comment_id):
    content = "you post a illegal comment %s" % comment_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = user_id
    notifi.theme_id = theme_id
    notifi.title = "您发了违规评论"
    notifi.post_id = post_id
    notifi.comment_id = comment_id
    notifi.content = content
    notifi.save()
    save2redis(notifi)


@app.task
def publish_illegal_comment(user_id, theme_id, post_id, comment_id):
    content = "you post a illegal comment %s" % comment_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = user_id
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.comment_id = comment_id
    notifi.content = content
    notifi.save()


@app.task
def ban_user(user_id, ban_days):
    """封禁用户"""
    log.info("Warning! user %s has been frozen " % user_id)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = user_id
    if ban_days:
        notifi.title = "您已被禁言%s天" % ban_days
        notifi.content = "下次注意!"
    else:
        notifi.title = "您已被永久禁言"
        notifi.content = ""
    notifi.save()
    save2redis(notifi)


@app.task
def unban_user(user_id, level_str):
    """解锁封禁用户"""
    user = connection.Users.find_one({'_id': ObjectId(user_id)})
    user.user_level_id = level_str
    user.save()
    log.info("unblock user %s" % user_id)
    notifi = connection.Notifications()
    notifi.type = "user"
    notifi.user_id = user_id
    notifi.title = "您已被解除禁言"
    notifi.content = "下次注意!"
    notifi.save()
    save2redis(notifi)


@app.task
def update_system(user_id, version):
    content = "Great news, you have a new version %s can be updated" % version
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def check_image(bucket, image_id, author):
    content = "check image: %s/%s" % (bucket, image_id)
    log.info(content)
    img_url = oc.bucket.sign_url("GET", bucket + '/' + image_id, 60)
    label, rate = detection.detect(img_url)
    if label:
        detect = connection.Detections()
        detect._id = image_id
        detect.author = author
        detect.bucket = bucket
        detect.save()
        log.info("rate is %s, image: %s/%s need to be checked again" % (rate, bucket, image_id))
        notifi = connection.Notifications()
        notifi.type = "system"
        notifi.user_id = author
        notifi.content = "您上传的图片有问题"
        notifi.save()


@app.task
def bind_cellphone(user_id, cellphone):
    content = "you have binded cellphone %s" % cellphone
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.content = content
    notifi.user_id = user_id
    notifi.save()


@app.task
def publish_porn_image(user_id, image_id):
    content = "you post a illegal porn image %s" % image_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "system"
    notifi.content = content
    notifi.user_id = user_id
    notifi.save()
