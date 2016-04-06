from tasks import app

@app.task
def new_reply(author_id, theme_id, post_id, comment_id):
    print("your post %s have a new comment" % post_id)


@app.task
def level_up(user):
    print("level up! %s" % user)
