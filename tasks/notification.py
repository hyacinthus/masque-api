import logging

from tasks import app
from model import connection
from log import app_log

log = logging.getLogger("masque.task.notifications")


@app.task
def new_reply(author_id, theme_id, post_id, comment_id):
    content = "Your post %s have a new comment %s" % (post_id, comment_id)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "comment"
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.user_id = author_id
    notifi.content = content
    notifi.save()


@app.task
def star_new_reply(author_id, theme_id, post_id, comment_id):
    content = "There are new comments %s for the post %s you viewed" % (post_id, comment_id)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "comment"
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.user_id = author_id
    notifi.content = content
    notifi.save()


@app.task
def comment_new_reply(author_id, theme_id, post_id, comment_id):
    content = "There are new comments %s for the post %s you remarked" % (comment_id, post_id)
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
    content = "Your post %s have a new heart" % post_id
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "message"
    notifi.user_id = author_id
    notifi.theme_id = theme_id
    notifi.post_id = post_id
    notifi.content = content
    notifi.save()


@app.task
def level_up(user_id, user_level):
    content = "Level up! your new level is %s" % user_level
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "levelup"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()


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
    content = "Thanks, your feedback %s have solved, exp +%s" % (exp, name)
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
def publish_invalid_report(author_id, theme_id, post_id, exp):
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
def publish_illegal_content(user_id, theme_id, post_id, exp):
    content = "you post a illegal content, exp %s" % exp
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "punishment"
    notifi.user_id = user_id
    notifi.theme_id = theme_id
    notifi.post_id = post_id
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
def check_image(bucket, id):
    content = "check image %s/%s" % (bucket, id)
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "message"
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