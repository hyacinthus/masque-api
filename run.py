from bson.json_util import dumps
from flask import Flask, make_response, jsonify
from flask_restful import Api

from model import connection
from resources.board_comment import BoardComment, BoardCommentList
from resources.board_post import BoardPost, BoardPostList
from resources.comment import Comment, CommentList
from resources.device import Device, DeviceList
from resources.device_trace import DeviceTrace, DeviceTraceList
from resources.mask import Mask, MaskList
from resources.message import Message, MessageList
from resources.parameter import Parameter, ParameterList
from resources.post import Post, PostList
from resources.theme import Theme, ThemeList
from resources.user import User, UserList
from resources.user_level import UserLevel, UserLevelList
from resources.user_trace import UserTrace, UserTraceList


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

api.add_resource(ThemeList, '/themes', endpoint='themes')
api.add_resource(Theme, '/themes/<string:theme_id>',
                 endpoint='theme')

api.add_resource(DeviceList, '/devices', endpoint='devices')
api.add_resource(Device, '/devices/<string:device_id>',
                 endpoint='device')

api.add_resource(UserLevelList, '/user_levels', endpoint='user_levels')
api.add_resource(UserLevel, '/user_levels/<string:user_level_id>',
                 endpoint='user_level')

api.add_resource(MaskList, '/masks', endpoint='masks')
api.add_resource(Mask, '/masks/<string:mask_id>',
                 endpoint='mask')

api.add_resource(BoardPostList, '/board_posts', endpoint='board_posts')
api.add_resource(BoardPost, '/board_posts/<string:board_post_id>',
                 endpoint='board_post')

api.add_resource(BoardCommentList, '/board_comments', endpoint='board_comments')
api.add_resource(BoardComment, '/board_comments/<string:board_comment_id>',
                 endpoint='board_comment')

api.add_resource(ParameterList, '/parameters', endpoint='parameters')
api.add_resource(Parameter, '/parameters/<string:parameter_id>',
                 endpoint='parameter')

api.add_resource(DeviceTraceList, '/device_traces', endpoint='device_traces')
api.add_resource(DeviceTrace, '/device_traces/<string:device_trace_id>',
                 endpoint='device_trace')

api.add_resource(MessageList, '/messages', endpoint='messages')
api.add_resource(Message, '/messages/<string:message_id>',
                 endpoint='message')

api.add_resource(UserTraceList, '/user_traces', endpoint='user_traces')
api.add_resource(UserTrace, '/user_traces/<string:user_trace_id>',
                 endpoint='user_trace')

if __name__ == '__main__':
    app.run()
