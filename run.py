from bson.json_util import dumps
from flask import Flask, make_response, jsonify, url_for
from flask_restful import Api

from model import connection
from resources.board_comment import BoardComments, BoardCommentsList
from resources.board_post import BoardPosts, BoardPostsList
from resources.comment import Comments, CommentsList, PostComments
from resources.device import Devices, DevicesList
from resources.device_trace import DeviceTrace, DeviceTraceList
from resources.mask import Masks, MasksList
from resources.message import Messages, MessagesList
from resources.parameter import Parameters, ParametersList
from resources.post import Posts, PostsList, FavorPost
from resources.theme import Themes, ThemesList
from resources.user import Users, UsersList, UserPostsList, UserCommentsList, \
    UserStarsList
from resources.user_level import UserLevels, UserLevelsList
from resources.user_trace import UserTraces, UserTracesList
from resources.location import SchoolsList


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


api.add_resource(PostsList, '/theme/<string:theme_id>/posts',
                 '/theme/<string:theme_id>/posts/',
                 endpoint='posts')
api.add_resource(Posts, '/theme/<string:theme_id>/post/<string:post_id>',
                 '/theme/<string:theme_id>/post/<string:post_id>/',
                 endpoint='post')
api.add_resource(FavorPost, '/post/<string:post_id>/star',
                 '/post/<string:post_id>/star/',
                 endpoint='post_star')

api.add_resource(CommentsList, '/theme/<string:theme_id>/comments',
                 '/theme/<string:theme_id>/comments/',
                 endpoint='comments')
api.add_resource(PostComments,
                 '/theme/<string:theme_id>/post/<string:post_id>/comments',
                 '/theme/<string:theme_id>/post/<string:post_id>/comments/',
                 endpoint='post_comment')
api.add_resource(Comments,
                 '/theme/<string:theme_id>/comment/<string:comment_id>',
                 '/theme/<string:theme_id>/comment/<string:comment_id>/',
                 endpoint='comment')

api.add_resource(UsersList, '/users', '/users/', endpoint='users')
api.add_resource(Users, '/users/<string:user_id>',
                 endpoint='user')

api.add_resource(UserPostsList, '/user/<string:user_id>/posts',
                 '/user/<string:user_id>/posts/',
                 endpoint='user_posts')
api.add_resource(UserCommentsList, '/user/<string:user_id>/comments',
                 '/user/<string:user_id>/comments/',
                 endpoint='user_comments')
api.add_resource(UserStarsList, '/user/<string:user_id>/stars',
                 '/user/<string:user_id>/stars/',
                 endpoint='user_stars')

api.add_resource(ThemesList, '/themes', endpoint='themes')
api.add_resource(Themes, '/themes/<string:theme_id>',
                 endpoint='theme')

api.add_resource(DevicesList, '/devices', endpoint='devices')
api.add_resource(Devices, '/devices/<string:device_id>',
                 endpoint='device')

api.add_resource(UserLevelsList, '/user_levels', endpoint='user_levels')
api.add_resource(UserLevels, '/user_levels/<string:user_level_id>',
                 endpoint='user_level')

api.add_resource(MasksList, '/masks', endpoint='masks')
api.add_resource(Masks, '/masks/<string:mask_id>',
                 endpoint='mask')

api.add_resource(BoardPostsList, '/board_posts', endpoint='board_posts')
api.add_resource(BoardPosts, '/board_posts/<string:board_post_id>',
                 endpoint='board_post')

api.add_resource(BoardCommentsList, '/board_comments',
                 endpoint='board_comments')
api.add_resource(BoardComments, '/board_comments/<string:board_comment_id>',
                 endpoint='board_comment')

api.add_resource(ParametersList, '/parameters', endpoint='parameters')
api.add_resource(Parameters, '/parameters/<string:parameter_id>',
                 endpoint='parameter')

api.add_resource(DeviceTraceList, '/device_traces', endpoint='device_traces')
api.add_resource(DeviceTrace, '/device_traces/<string:device_trace_id>',
                 endpoint='device_trace')

api.add_resource(MessagesList, '/messages', endpoint='messages')
api.add_resource(Messages, '/messages/<string:message_id>',
                 endpoint='message')

api.add_resource(UserTracesList, '/user_traces', endpoint='user_traces')
api.add_resource(UserTraces, '/user_traces/<string:user_trace_id>',
                 endpoint='user_trace')

api.add_resource(SchoolsList, '/location/<lng>/<lat>/schools', endpoint='schools')

if __name__ == '__main__':
    app.run()
