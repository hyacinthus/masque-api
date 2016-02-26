from datetime import datetime

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, request, make_response, jsonify
from flask_pymongo import PyMongo
from flask_restful import Api, Resource, abort

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py', silent=True)
    return app


app = create_app()
mongo = PyMongo(app, config_prefix='MONGO')
api = Api(app)


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'message': 'Not found'}), 404)


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    return obj


class GeoPostList(Resource):
    def get(self):  # get all posts
        cursor = mongo.db.geo_posts.find({})
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        resp["_created"] = datetime.utcnow()
        mongo.db.geo_posts.insert(resp)
        return "", 201


class GeoPost(Resource):
    def get(self, post_id):  # get a post by its ID
        cursor = mongo.db.geo_posts.find({"_id": ObjectId(post_id)})
        return check_content(cursor)

    def put(self, post_id):  # update a post by its ID
        resp = request.get_json(force=True)
        cursor = mongo.db.geo_posts.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$set": resp
            }
        )
        return "", 204

    def delete(self, post_id):  # delete a post by its ID
        cursor = mongo.db.geo_posts.remove({"_id": ObjectId(post_id)})
        # delete related comments
        cursor = mongo.db.geo_comments.remove({"post_id": post_id})
        return "", 204


class GeoCommentList(Resource):
    def get(self):  # get all comments
        cursor = mongo.db.geo_comments.find({})
        return check_content(cursor)

    def post(self):  # add a new comment
        resp = request.get_json(force=True)
        resp["_created"] = datetime.utcnow()
        mongo.db.geo_comments.insert(resp)
        return "", 201


class GeoComment(Resource):
    def get(self, comment_id):  # get a comment by its ID
        cursor = mongo.db.geo_comments.find({"_id": ObjectId(comment_id)})
        return check_content(cursor)

    def put(self, comment_id):  # update a comment by its ID
        resp = request.get_json(force=True)
        cursor = mongo.db.geo_comments.update_one(
            {"_id": ObjectId(comment_id)},
            {
                "$set": resp
            }
        )
        return "", 204

    def delete(self, comment_id):  # delete a comment by its ID
        cursor = mongo.db.geo_comments.remove({"_id": ObjectId(comment_id)})
        return "", 204


api.add_resource(GeoPostList, '/geo_posts', endpoint='geo_posts')
api.add_resource(GeoPost, '/geo_posts/<string:post_id>',
                 endpoint='geo_post')
api.add_resource(GeoCommentList, '/geo_comments', endpoint='geo_comments')
api.add_resource(GeoComment, '/geo_comments/<string:comment_id>',
                 endpoint='geo_comment')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
