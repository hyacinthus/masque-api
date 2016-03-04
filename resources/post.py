from bson.objectid import ObjectId
from flask_restful import Resource, abort, request, reqparse

from config import MongoConfig, APIConfig
from model import connection


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    elif obj.count() == 1:
        return obj[0]  # return a dict if obj has only one item
    return obj  # or return a list


class PostList(Resource):
    def get(self, theme_id):  # get all posts
        parser = reqparse.RequestParser()
        parser.add_argument('page',
                            type=int,
                            help='page number must be int')
        args = parser.parse_args()
        if args['page'] is None:
            args['page'] = 1
        index = args['page'] - 1
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Post.find(
            skip=(index * APIConfig.PAGESIZE),
            limit=APIConfig.PAGESIZE,
            max_scan=APIConfig.MAX_SCAN,
            sort=[("_updated", -1)])  # sorted by update time in reversed order
        return check_content(cursor)

    def post(self, theme_id):  # add a new post
        resp = request.get_json(force=True)
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        doc = collection.Post()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc['_id'] = str(ObjectId())
        doc.save()
        return {"_id": doc['_id']}, 201


class Post(Resource):
    def get(self, theme_id, post_id):  # get a post by its ID
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Post.find({"_id": ObjectId(post_id)})
        return check_content(cursor)

    def put(self, theme_id, post_id):  # update a post by its ID
        resp = request.get_json(force=True)
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        doc = collection.Post()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = post_id
        doc.save()
        return None, 204

    def delete(self, theme_id, post_id):  # delete a post by its ID
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        collection.Post.find_and_modify(
            {"_id": ObjectId(post_id)}, remove=True)
        # delete related comments
        collection.Comment.find_and_modify(
            {"post_id": ObjectId(post_id)}, remove=True)
        return None, 204
