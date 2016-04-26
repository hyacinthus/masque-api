import logging

from model import connection
from tasks import app

log = logging.getLogger("masque.task.event")


@app.task
def post_log(user_id, theme_id, post_id, create_time):
    content = "user %s have new post %s" % (user_id, post_id)
    log.info(content)
    post = connection.PostLog()
    post.user_id = user_id
    post.theme_id = theme_id
    post.post_id = post_id
    post._created = create_time
    post.save()


@app.task
def comment_log(user_id, theme_id, post_id, comment_id, create_time):
    content = "user %s have posted new remark %s" % (user_id, comment_id)
    log.info(content)
    comment = connection.CommentLog()
    comment.user_id = user_id
    comment.theme_id = theme_id
    comment.post_id = post_id
    comment.comment_id = comment_id
    comment._created = create_time
    comment.save()


@app.task
def sign_up_log(user_id, device_id, create_time):
    content = "user %s registered on %s" % (user_id, create_time)
    log.info(content)
    signup = connection.SignUpLog()
    signup.user_id = user_id
    signup.device_id = device_id
    signup._created = create_time
    signup.save()


@app.task
def sign_in_log(user_id, device_id, update_time):
    content = "user %s login on %s" % (user_id, update_time)
    log.info(content)
    signin = connection.SignInLog()
    signin.user_id = user_id
    signin.device_id = device_id
    signin._created = update_time
    signin.save()


@app.task
def geo_request_log(user_id, location):
    content = "user %s update location %s" % (user_id, location.district)
    log.info(content)
    geo = connection.GeoRequestLog()
    geo.user_id = user_id
    geo.location.province = location.province
    geo.location.city = location.city
    geo.location.district = location.district
    geo.save()

