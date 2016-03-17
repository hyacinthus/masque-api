from bson.json_util import dumps
from flask import Flask, make_response, jsonify
from flask_restful import Api

from model import connection
from resources import *


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
api.add_resource(Post, '/theme/<string:theme_id>/post/<string:post_id>',
                 '/theme/<string:theme_id>/post/<string:post_id>/',
                 endpoint='post')
api.add_resource(Hearts,
                 '/theme/<string:theme_id>/post/<string:post_id>/hearts',
                 '/theme/<string:theme_id>/post/<string:post_id>/hearts/',
                 endpoint='hearts')
api.add_resource(FavorPost,
                 '/theme/<string:theme_id>/post/<string:post_id>/star',
                 '/theme/<string:theme_id>/post/<string:post_id>/star/',
                 endpoint='post_star')

api.add_resource(CommentsList, '/theme/<string:theme_id>/comments',
                 '/theme/<string:theme_id>/comments/',
                 endpoint='comments')
api.add_resource(PostComments,
                 '/theme/<string:theme_id>/post/<string:post_id>/comments',
                 '/theme/<string:theme_id>/post/<string:post_id>/comments/',
                 endpoint='post_comment')
api.add_resource(Comment,
                 '/theme/<string:theme_id>/comment/<string:comment_id>',
                 '/theme/<string:theme_id>/comment/<string:comment_id>/',
                 endpoint='comment')

api.add_resource(UsersList, '/users', '/users/', endpoint='users')
api.add_resource(User, '/user/<string:user_id>', '/user/<string:user_id>/',
                 endpoint='user')
api.add_resource(DeviceUser, '/device/<string:device_id>/user',
                 '/device/<string:device_id>/user/',
                 endpoint='device_user')

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
api.add_resource(Theme, '/theme/<string:theme_id>',
                 endpoint='theme')

api.add_resource(DevicesList, '/devices', endpoint='devices')
api.add_resource(Device, '/device/<string:device_id>',
                 endpoint='device')

api.add_resource(UserLevelsList, '/user_levels', endpoint='user_levels')
api.add_resource(UserLevel, '/user_level/<string:user_level_id>',
                 endpoint='user_level')

api.add_resource(MasksList, '/masks', endpoint='masks')
api.add_resource(Mask, '/mask/<string:mask_id>',
                 endpoint='mask')

api.add_resource(BoardPostsList, '/board_posts', endpoint='board_posts')
api.add_resource(BoardPost, '/board_post/<string:board_post_id>',
                 endpoint='board_post')

api.add_resource(BoardCommentsList, '/board_comments',
                 endpoint='board_comments')
api.add_resource(BoardComment, '/board_comment/<string:board_comment_id>',
                 endpoint='board_comment')

api.add_resource(ParametersList, '/parameters', endpoint='parameters')
api.add_resource(Parameter, '/parameter/<string:parameter_id>',
                 endpoint='parameter')

api.add_resource(DeviceTraceList, '/device_traces', endpoint='device_traces')
api.add_resource(DeviceTrace, '/device_trace/<string:device_trace_id>',
                 endpoint='device_trace')

api.add_resource(MessagesList, '/messages', endpoint='messages')
api.add_resource(Message, '/message/<string:message_id>',
                 endpoint='message')

api.add_resource(UserTracesList, '/user_traces', endpoint='user_traces')
api.add_resource(UserTrace, '/user_trace/<string:user_trace_id>',
                 endpoint='user_trace')

api.add_resource(SchoolsList, '/location/schools',
                 endpoint='schools')

if __name__ == '__main__':
    app.run()
