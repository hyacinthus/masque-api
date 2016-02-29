from bson.json_util import dumps
from flask import Flask, make_response, jsonify
from flask_restful import Api

from comment import GeoComment, GeoCommentList
from post import GeoPost, GeoPostList
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


api.add_resource(GeoPostList, '/geo_posts', endpoint='geo_posts')
api.add_resource(GeoPost, '/geo_posts/<string:post_id>',
                 endpoint='geo_post')
api.add_resource(GeoCommentList, '/geo_comments', endpoint='geo_comments')
api.add_resource(GeoComment, '/geo_comments/<string:comment_id>',
                 endpoint='geo_comment')
api.add_resource(UserList, '/users', endpoint='users')
api.add_resource(User, '/users/<string:user_id>',
                 endpoint='user')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
