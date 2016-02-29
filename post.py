from flask_restful import Resource, abort, request

from model import *


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    elif obj.count() == 1:
        return obj[0]  # return a dict if obj has only one item
    return obj  # or return a list


class GeoPostList(Resource):
    def get(self):  # get all posts
        cursor = connection.GeoPost.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.GeoPost()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return "", 201


class GeoPost(Resource):
    def get(self, post_id):  # get a post by its ID
        cursor = connection.GeoPost.find({"_id": ObjectId(post_id)})
        return check_content(cursor)

    def put(self, post_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.GeoPost()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = post_id
        doc.save()
        return "", 204

    def delete(self, post_id):  # delete a post by its ID
        cursor = connection.GeoPost.find_and_modify(
            {"_id": ObjectId(post_id)}, remove=True)
        # delete related comments
        # cursor = db.geo_comments.remove({"post_id": post_id})
        return "", 204
