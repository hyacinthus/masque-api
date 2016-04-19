import logging
from datetime import datetime

from bson.objectid import ObjectId
from flask_restful import Resource, request, reqparse

from config import MongoConfig, APIConfig
from model import connection, TokenResource, CheckPermission
from paginate import Paginate
from util import add_exp

log = logging.getLogger("masque.comment")


class PostsList(TokenResource):
    def get(self, theme_id):  # get all posts
        parser = reqparse.RequestParser()
        parser.add_argument('page',
                            type=int,
                            help='page number must be int')

        parser.add_argument('count',
                            type=int,
                            help='count must be int')
        args = parser.parse_args()
        page = 1 if not args['page'] else args['page']
        if not args['count']:
            limit = APIConfig.PAGESIZE
        else:
            limit = args['count']
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Posts.find(
            max_scan=APIConfig.MAX_SCAN,
            sort=[("_updated", -1)]
        )  # 按回帖时间排序
        paged_cursor = Paginate(cursor, page, limit)
        return paged_cursor.data

    def post(self, theme_id):  # add a new post
        # 权限检测
        perm = CheckPermission(self.user_info.user._id)
        if perm.post < self.limit_info.post_limit:
            # 经验限制(每发一帖经验加5, 每日上限10)
            if perm.exp <= 5:
                user = self.user_info.user
                add_exp(user, 5)
                perm.exp = 5  # 经验记数加 5
                user.save()
            perm.post = 1  # 没有超额, 允许发帖, 同时发帖数加 1
        else:
            return {
                       "message": "今日发帖数量已到上限, 大侠还请明日再来"
                   }, 403
        utctime = datetime.timestamp(datetime.utcnow())
        resp = request.get_json(force=True)
        # save a post
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        doc = collection.Posts()
        for item in resp:
            if item in ('mask_id', 'author', '_created', '_updated'):
                continue
            doc[item] = resp[item]
        doc['_created'] = utctime
        doc['_updated'] = utctime
        doc['mask_id'] = self.user_info.user.masks[0]
        doc['author'] = self.user_info.user._id
        doc.save()
        # save a record
        user_posts = connection.UserPosts()
        user_posts['user_id'] = doc['author']
        user_posts['theme_id'] = theme_id
        user_posts['post_id'] = doc['_id']
        user_posts['_created'] = utctime
        user_posts.save()
        return {"_id": doc['_id']}, 201  # return post_id generated by system


class Post(Resource):
    def get(self, theme_id, post_id):  # get a post by its ID
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Posts.find_one({"_id": ObjectId(post_id)})
        return cursor

    def put(self, theme_id, post_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        collection.Posts.find_and_modify(
            {"_id": ObjectId(post_id)},
            {
                "$set": resp
            }
        )
        return '', 204

    def delete(self, theme_id, post_id):  # delete a post by its ID
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        collection.Posts.find_and_modify(
            {"_id": ObjectId(post_id)}, remove=True)
        # delete related comments
        collection.Comments.find_and_modify(
            {"post_id": ObjectId(post_id)}, remove=True)
        return '', 204


class FavorPost(TokenResource):
    def post(self, theme_id, post_id):
        cursor = connection.UserStars.find_one(
            {
                "post_id": post_id,
                "user_id": self.user_info.user._id,
                "theme_id": theme_id
            }
        )
        # 检测帖子是否已被收藏
        if not cursor:  # do nothing if repeatedly submits happened
            connection.UserStars.find_and_modify(
                {
                    "post_id": post_id,
                    "user_id": self.user_info.user._id,
                    "theme_id": theme_id
                },
                {
                    "post_id": post_id,
                    "user_id": self.user_info.user._id,
                    "theme_id": theme_id
                },
                upsert=True
            )
            return '', 201
        else:
            return {
                       "status": "error",
                       "message": "你已经收藏过这个帖子了"
                   }, 422

    def delete(self, theme_id, post_id):
        connection.UserStars.find_and_modify(
            {
                "post_id": post_id,
                "user_id": self.user_info.user._id,
                "theme_id": theme_id
            },
            remove=True
        )
        return '', 204


class Hearts(TokenResource):
    def post(self, theme_id, post_id):
        # 权限检测
        perm = CheckPermission(self.user_info.user._id)
        if perm.heart < self.limit_info.heart_limit:
            perm.heart = 1  # 没有超额, 允许感谢, 同时感谢数加 1
        else:
            return {
                       "message": "今天发出的感谢已经够多了, 亲先歇歇吧"
                   }, 403
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Posts.find_one({"_id": ObjectId(post_id)})
        # 感谢不能送给自己
        if cursor['author'] == self.user_info.user._id:
            return {
                       "status": "error",
                       "message": "感谢不能送给自己!"
                   }, 422
        # 查找用户是否已经感谢过这个帖子
        for item in cursor['hearts']:
            if item['user_id'] == self.user_info.user._id:
                return {
                           "status": "error",
                           "message": "你已经感谢过这个帖子!"
                       }, 422
        # 更新 hearts 列表
        collection.Posts.find_and_modify(
            {"_id": ObjectId(post_id)},
            {
                "$addToSet": {
                    "hearts": {
                        "user_id": self.user_info.user._id,
                        "mask_id": self.user_info.user.masks[0]
                    }
                }
            }
        )
        user = connection.Users.find_one({"_id": ObjectId(cursor['author'])})
        # 给帖子作者 hearts_received 加一
        user.hearts_received += 1
        # 给帖子作者加 10 经验
        add_exp(user, 10)
        user.save()
        return '', 201


class Feedback(TokenResource):
    """反馈"""
    def post(self):
        resp = request.get_json(force=True)
        doc = connection.Feedback()
        for item in resp:
            doc[item] = resp[item]
        doc.author = self.user_info.user._id
        doc.save()
        return '', 201


class ReportPost(TokenResource):
    """举报"""
    def post(self, theme_id, post_id):
        # 权限检测
        perm = CheckPermission(self.user_info.user._id)
        if perm.report < self.limit_info.report_limit:
            perm.report = 1  # 没有超额, 允许举报, 同时举报数加 1
        else:
            return {
                       "message": "今日举报的次数已达上限, 谢谢支持!"
                   }, 403
        # 判断被举报的帖子存在与否
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Posts.find_one({"_id": ObjectId(post_id)})
        if not cursor:
            return {
                       "status": "error",
                       "message": "您举报的帖子已被删除, 谢谢支持!"
                   }, 404
        else:
            # 存在则取到author值
            author = cursor.author
        current_user = self.user_info.user._id
        # 检查是否有此举报
        cursor = connection.ReportPosts.find_one(
            {
                "theme_id": theme_id,
                "post_id": post_id
            }
        )
        if not cursor:
            # 不存在就新建
            new_report = connection.ReportPosts()
            new_report.author = author
            new_report.theme_id = theme_id
            new_report.post_id = post_id
            new_report.reporters = [current_user]
            new_report.save()
            return '', 201
        elif current_user not in cursor.reporters:
            # 当前用户没有举报则可以举报, 只需要在 reporters 列表加入当前用户 id 即可
            connection.ReportPosts.find_and_modify(
                {
                    "theme_id": theme_id,
                    "post_id": post_id
                },
                {
                    "$addToSet": {
                        "reporters": current_user
                    },
                    "$set": {
                        "_updated": datetime.utcnow()
                    }
                }
            )
            return '', 201
        else:
            return {
                       "status": "error",
                       "message": "你已经举报过该帖子了, 谢谢支持!"
                   }, 422
