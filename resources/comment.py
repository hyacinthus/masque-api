import logging
from datetime import datetime

from bson.objectid import ObjectId
from flask_restful import request, reqparse

from config import MongoConfig, APIConfig
from model import connection, TokenResource, CheckPermission
from paginate import Paginate
from util import add_exp, new_remark

log = logging.getLogger("masque.comment")


class CommentsList(TokenResource):
    def get(self, theme_id):  # get all comments
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
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        cursor = collection.Comments.find(
            sort=[("_created", -1)],
            max_scan=APIConfig.MAX_SCAN
        )
        paged_cursor = Paginate(cursor, page, limit)
        return paged_cursor.data

    def post(self, theme_id):  # add a new comment
        # 每条评论加 1 经验, 每日上限 10
        perm = CheckPermission(self.user_info.user._id)
        if perm.exp < 10:
            user = self.user_info.user
            add_exp(user, 1)
            perm.exp = 1  # 每日经验记数加 1
            user.save()
        # 当日评论数加 1
        perm.comment = 1
        utctime = datetime.timestamp(datetime.utcnow())
        resp = request.get_json(force=True)
        # save a comment
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        doc = collection.Comments()
        for item in resp:
            if item in ("_created", "mask_id", "author"):
                continue
            doc[item] = resp[item]
        doc['_created'] = utctime
        doc['author'] = self.user_info.user._id
        # 如果之前回复过该贴, 头像保持原状
        cursor = collection.find_one(
            {
                "post_id": resp["post_id"],
                "author": self.user_info.user._id
            }
        )
        if cursor:
            doc["mask_id"] = cursor["mask_id"]
        else:
            collection = connection[MongoConfig.DB]["posts_" + theme_id]
            cursor = collection.find_one({"_id": ObjectId(resp['post_id'])})
            if cursor["author"] == self.user_info.user._id:
                # 楼主回帖, 头像不变
                doc["mask_id"] = cursor["mask_id"]
            else:
                doc['mask_id'] = self.user_info.user.masks[0]
        doc.save()
        # save a record
        user_comments = connection.UserComments()
        user_comments['user_id'] = self.user_info.user._id
        user_comments['theme_id'] = theme_id
        user_comments['comment_id'] = doc['_id']
        user_comments['_created'] = utctime
        user_comments.save()
        # comment_count +1 when a new comment posted
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        collection.find_and_modify(
            {"_id": ObjectId(resp['post_id'])},
            {
                "$inc": {
                    "comment_count": 1
                },
                "$set": {
                    "_updated": datetime.utcnow()
                }
            }
        )
        new_remark(doc)  # 回帖提醒
        return {"_id": doc['_id']}, 201  # return comment_id generated by system


class Comment(TokenResource):
    def get(self, theme_id, comment_id):  # get a comment by its ID
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        cursor = collection.Comments.find_one({"_id": ObjectId(comment_id)})
        return cursor

    def put(self, theme_id, comment_id):  # update a comment by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        collection.Comments.find_and_modify(
            {"_id": ObjectId(comment_id)},
            {
                "$set": resp
            }
        )
        return '', 204

    def delete(self, theme_id, comment_id):  # delete a comment by its ID
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        collection.Comments.find_and_modify(
            {"_id": ObjectId(comment_id)}, remove=True)
        return '', 204


class PostComments(TokenResource):
    def get(self, theme_id, post_id):  # get a post's comments
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
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        cursor = collection.Comments.find(
            {
                "post_id": post_id
            },
            max_scan=APIConfig.MAX_SCAN
        )
        paged_cursor = Paginate(cursor, page, limit)
        return paged_cursor.data


class ReportComment(TokenResource):
    def post(self, theme_id, comment_id):
        # 权限检测
        perm = CheckPermission(self.user_info.user._id)
        if perm.report < self.limit_info.report_limit:
            perm.report = 1  # 没有超额, 允许举报, 同时举报数加 1
        else:
            return {
                       "message": "今日举报的次数已达上限, 谢谢支持!"
                   }, 403
        # 判断被举报的评论存在与否
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        cursor = collection.Comments.find_one({"_id": ObjectId(comment_id)})
        if not cursor:
            return {
                       "status": "error",
                       "message": "您举报的内容已被删除, 谢谢支持!"
                   }, 404
        else:
            # 存在则取到author值
            author = cursor.author
        current_user = self.user_info.user._id
        # 检查是否有此举报
        cursor = connection.ReportComments.find_one(
            {
                "theme_id": theme_id,
                "comment_id": comment_id
            }
        )
        if not cursor:
            # 不存在就新建
            new_report = connection.ReportComments()
            new_report.author = author
            new_report.theme_id = theme_id
            new_report.comment_id = comment_id
            new_report.reporters = [current_user]
            new_report.save()
            return '', 201
        elif current_user not in cursor.reporters:
            # 当前用户没有举报则可以举报
            connection.ReportComments.find_and_modify(
                {
                    "theme_id": theme_id,
                    "comment_id": comment_id
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


class CommentHeart(TokenResource):
    """感谢评论"""

    def post(self, theme_id, comment_id):
        # 权限检测
        user = self.user_info.user
        perm = CheckPermission(user._id)
        if user.hearts_owned > 0:
            # 感谢余额充足, 允许感谢, 同时当天感谢记数加 1, 拥有感谢数减 1
            user.hearts_owned -= 1
            user.save()
            perm.heart = 1
        else:
            return {
                       "message": "感谢数不足, 无法送出感谢"
                   }, 403
        # 判断要感谢的评论存在与否
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        cursor = collection.Comments.find_one({"_id": ObjectId(comment_id)})
        if not cursor:
            return {
                       "status": "error",
                       "message": "您要感谢的评论已被删除, 请刷新当前页面内容"
                   }, 404
        current_user = self.user_info.user._id
        cursor = connection.Users.find_one({"_id": ObjectId(current_user)})
        current_mask = cursor.masks[0]  # 此用户当前面具id

        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        cursor = collection.Comments.find_one({"_id": ObjectId(comment_id)})
        # 发帖人不能自己感谢自己
        if cursor.author == current_user:
            return {
                       "status": "error",
                       "message": "自己不能感谢自己哦"
                   }, 422
        # 查找用户是否已经感谢过这个帖子
        for item in cursor.hearts:
            if item['user_id'] == current_user:
                return {
                           "status": "error",
                           "message": "您已经感谢过这条评论了"
                       }, 422
        # 更新 hearts 列表
        collection.Comments.find_and_modify(
            {"_id": ObjectId(comment_id)},
            {
                "$addToSet": {
                    "hearts": {
                        "user_id": current_user,
                        "mask_id": current_mask
                    }
                }
            }
        )
        # 给评论作者 hearts_received 加一
        connection.Users.find_and_modify(
            {"_id": ObjectId(cursor['author'])},
            {
                "$inc": {
                    "hearts_received": 1
                }
            }
        )
        return '', 201
