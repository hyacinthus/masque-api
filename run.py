from bson.json_util import dumps
from flask import Flask, make_response, jsonify
from flask_restful import Api

from comment import Comment, CommentList
from model import connection
from post import Post, PostList
from user import User, UserList


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.FlaskConfig')
    app.config.from_pyfile('config.py', silent=True)
    return app


app = create_app()
api = Api(app)


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'message': 'Not found'}), 404)


@app.teardown_request
def teardown_request(exception):  # close db connection after each api request
    connection.close()


api.add_resource(PostList, '/posts_<string:theme_id>', endpoint='posts')
api.add_resource(Post, '/posts_<string:theme_id>/<string:post_id>',
                 endpoint='post')
api.add_resource(CommentList, '/comments_<string:theme_id>',
                 endpoint='comments')
api.add_resource(Comment, '/comments_<string:theme_id>/<string:comment_id>',
                 endpoint='comment')
api.add_resource(UserList, '/users', endpoint='users')
api.add_resource(User, '/users/<string:user_id>',
                 endpoint='user')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
