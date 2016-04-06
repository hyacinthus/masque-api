import logging

from tasks import app
from model import connection
from log import app_log

log = logging.getLogger("masque.task.notifications")
@app.task
def new_reply(author_id, theme_id, post_id, comment_id):
    log.info("your post %s have a new comment" % post_id)


@app.task
def level_up(user_id, user_level):
    content = "level up! your new level is %s" % user_level
    log.info(content)
    notifi = connection.Notifications()
    notifi.type = "levelup"
    notifi.user_id = user_id
    notifi.content = content
    notifi.save()
