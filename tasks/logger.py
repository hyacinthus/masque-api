import logging
from json import loads

from model import connection
from tasks import app

log = logging.getLogger("masque.task.logger")


@app.task
def user_post(dump_doc):
    """用户发帖记录表"""
    doc = loads(dump_doc)
    user_posts = connection.UserPosts()
    for i in doc:
        user_posts[i] = doc[i]
    user_posts.save()
    log.info('user_posts %s has been saved.' % user_posts._id)


@app.task
def post_log(dump_doc):
    """用户发帖日志"""
    doc = loads(dump_doc)
    post = connection.PostLog()
    for i in doc:
        post[i] = doc[i]
    post.save()
    log.info('user %s has published a new post %s' % (doc['user_id'], post._id))


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
    content = "user %s update location" % geo.user_id
    log.info(content)


@app.task
def posts_delete_log(dump_doc, exp_reduce, ban_days, admin, reason):
    report = loads(dump_doc)
    content = "user %s have reduced exp %s and banned post %s days" % \
              (report["author"], exp_reduce, ban_days)
    log.info(content)
    pdl = connection.PostsDeleteLog()
    pdl.theme_id = report["theme_id"]
    pdl.post_id = report["post_id"]
    pdl.author = report["author"]
    pdl.admin = admin
    pdl.reason = reason
    pdl.exp_reduce = exp_reduce
    pdl.ban_days = ban_days
    pdl.save()


@app.task
def comments_ban_log(dump_doc, exp_reduce, ban_days, admin, reason):
    report = loads(dump_doc)
    content = "user %s have reduced exp %s and banned post %s days" % \
              (report["author"], exp_reduce, ban_days)
    log.info(content)
    cbl = connection.CommentsBanLog()
    cbl.theme_id = report["theme_id"]
    cbl.post_id = report["post_id"]
    cbl.comment_id = report["comment_id"]
    cbl.author = report["author"]
    cbl.admin = admin
    cbl.reason = reason
    cbl.exp_reduce = exp_reduce
    cbl.ban_days = ban_days
    cbl.save()
