import logging
from json import loads

from model import connection
from tasks import app

log = logging.getLogger("masque.task.logger")


@app.task
def post_log(user_id, theme_id, post_id):
    content = "user %s have new post %s" % (user_id, post_id)
    log.info(content)
    post = connection.PostLog()
    post.user_id = user_id
    post.theme_id = theme_id
    post.post_id = post_id
    post.save()


@app.task
def comment_log(user_id, theme_id, post_id, comment_id):
    content = "user %s have posted new remark %s" % (user_id, comment_id)
    log.info(content)
    comment = connection.CommentLog()
    comment.user_id = user_id
    comment.theme_id = theme_id
    comment.post_id = post_id
    comment.comment_id = comment_id
    comment.save()


@app.task
def sign_up_log(user_id, device_id):
    signup = connection.SignUpLog()
    signup.user_id = user_id
    signup.device_id = device_id
    signup.save()
    content = "new user %s login up" % (user_id)
    log.info(content)


@app.task
def sign_in_log(user_id, device_id):
    signin = connection.SignInLog()
    signin.user_id = user_id
    signin.device_id = device_id
    signin.save()
    content = "user %s login in" % (signin._id)
    log.info(content)


@app.task
def geo_request_log(geo_info):
    geo_info = loads(geo_info)
    geo = connection.GeoRequestLog()
    for i in geo_info:
        geo[i] = geo_info[i]
    geo.save()
    content = "user %s update location" % (geo.user_id)
    log.info(content)


@app.task
def posts_delete_log(theme_id):
    pdl = connection.Posts_Delete_Log()
    pdl.theme_id = theme_id
    pass


@app.task
def comments_ban_log():
    pass
