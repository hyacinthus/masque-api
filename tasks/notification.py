import logging

from tasks import app
from model import connection
from log import app_log

log = logging.getLogger("masque.task.notifications")


@app.task
def new_reply(author_id, post_id, comment_id):
    content = "your post %s have a new comment %s" % (post_id, comment_id)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "message"
    notifi.user_id = author_id
    notifi.content = content
    notifi.save()


@app.task
def new_heart(author_id, post_id):
    content = "your post %s have a new heart" % post_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "message"
    notifi.user_id = author_id
    notifi.content = content
    notifi.save()


@app.task
def level_up(user_id, user_level):
    content = "level up! your new level is %s" % user_level
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "levelup"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def level_down(user_id, user_level):
    content = "level down! your new level is %s" % user_level
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def forbid_post(user_id, expiry=7*24*3600):
    content = "punishment! you are prohibited to post %s" % expiry
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def frozen_user(user_id):
    content = "punishment! your account has been frozen "
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def exp_up(user_id, user_exp):
    content = "congratulation! your exp up to %s " % user_exp
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "encourage"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


@app.task
def update_system(user_id, version):
    content = "great news, you have a new version %s can be updated" % version
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "message"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()
