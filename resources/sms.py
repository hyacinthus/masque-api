import logging
import random
import re

from bson.objectid import ObjectId
from flask_restful import Resource, reqparse

import top.api
from config import AliConfig
from model import redisdb, connection, TokenResource
from util import add_exp

log = logging.getLogger("masque.sms")


def send_sms(phone, code):
    """发送验证码"""
    req = top.api.AlibabaAliqinFcSmsNumSendRequest()
    req.set_app_info(top.appinfo(AliConfig.SMS_IKEY, AliConfig.SMS_AKEY))
    req.sms_type = AliConfig.SMS_TYPE
    req.rec_num = phone
    req.sms_template_code = AliConfig.SMS_TEMPLATE_CODE
    req.sms_free_sign_name = AliConfig.SMS_FREE_SIGN_NAME
    req.sms_param = {
        "code": code,
        "product": AliConfig.APP_NAME,
        "ttl": str(AliConfig.SMS_TTL)
    }
    try:
        resp = req.getResponse()
    except:
        return None
    return resp


def generate_verification_code(code_length=6):
    """生成任意位随机数"""
    code_list = random.sample([str(i) for i in range(10)], code_length)
    return "".join(code_list)


def verify_phone(phone):
    """正则匹配手机号码"""
    pattern = re.compile('^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}')
    return pattern.match(phone)


class RequestSmsCode(Resource):
    def post(self, cellphone):
        if not verify_phone(cellphone):
            return {
                       "status": "error",
                       'message': '手机号码格式错误，请重新输入'
                   }, 403
        verify_code = generate_verification_code(4)  # 生成4位随机数验证码
        resp = send_sms(cellphone, verify_code)
        if resp and resp["alibaba_aliqin_fc_sms_num_send_response"]["result"][
            "err_code"] == "0":
            if redisdb.lpush(
                    "sms_verify:{}".format(cellphone),
                    verify_code
            ):
                if redisdb.ttl("sms_verify:{}".format(cellphone)) == -1:
                    # 设置超时时间
                    redisdb.expire("sms_verify:{}".format(cellphone),
                                   AliConfig.SMS_TTL * 60)
                return {
                           "status": "ok",
                           "message": "验证码已发送"
                       }, 201
            else:
                return {
                           "status": "error",
                           "message": "短信验证服务出错，请稍后再试"
                       }, 403
        else:
            return {
                       "status": "error",
                       "message": "短信验证服务出错，请稍后再试"
                   }, 403


class VerifySmsCode(Resource):
    def post(self, cellphone):
        if not verify_phone(cellphone):
            return {
                       'message': '手机号码格式错误，请重新输入',
                       "status": "error"
                   }, 403
        parser = reqparse.RequestParser()
        parser.add_argument('code',
                            type=str,
                            required=True,
                            help='verify_code not found')
        args = parser.parse_args()
        user_code = args['code']
        if not redisdb.exists("sms_verify:{}".format(cellphone)):
            return {
                       "status": "error",
                       "message": "验证码已过期"
                   }, 403
        sys_code = redisdb.lrange("sms_verify:{}".format(cellphone), 0, -1)
        if user_code in sys_code:
            return {
                       "status": "ok",
                       "message": "验证码匹配正确"
                   }, 201
        else:
            return {
                       "status": "error",
                       "message": "验证码错误，请重试"
                   }, 403


class BoundPhone(TokenResource):
    """绑定手机"""

    def post(self, cellphone):
        if not verify_phone(cellphone):
            return {
                       'message': '手机号码格式错误，请重新输入',
                       "status": "error"
                   }, 403
        current_user_id = self.user_info.user._id
        cursor = connection.Users.find_one(
            {"cellphone": cellphone}
        )
        if cursor:
            # 绑定过手机, 将当前设备匹配到先前绑定手机用户
            if current_user_id == cursor._id:
                # 号码未变, 不做处理
                return {
                           "status": "error",
                           'message': '你已经绑定过这个号码了'
                       }, 403
            # 把先前绑定手机用户id赋给当前设备
            connection.Devices.find_and_modify(
                {"_id": self.user_info.device_id},
                {
                    "$set": {
                        "user_id": cursor._id
                    }
                }
            )
            user = connection.Users.find_one({"_id": ObjectId(cursor._id)})
            return {
                       "status": "ok",
                       "data": user,
                       "message": "欢迎回来，将为您恢复此手机之前关联的资料"
                   }, 201
        else:
            # 没有绑定过手机, 将cellphone填入当前user_id.cellphone字段
            connection.Users.find_and_modify(
                {"_id": ObjectId(current_user_id)},
                {
                    "$set": {"cellphone": cellphone}
                }
            )
            user = connection.Users.find_one({"_id": ObjectId(current_user_id)})
            # 绑定手机加 20 经验
            add_exp(user, 20)
            user.save()
            return {
                       "status": "ok",
                       "data": user,
                       "message": "手机号码绑定成功"
                   }, 201


class ChangePhone(TokenResource):
    """更换手机"""

    def post(self, cellphone):
        if not verify_phone(cellphone):
            return {
                       'message': '手机号码格式错误，请重新输入',
                       "status": "error"
                   }, 403
        current_user_id = self.user_info.user._id
        cursor = connection.Users.find_one({"cellphone": cellphone})
        if cursor:
            # 号码之前有使用过, 提示该手机号码已被使用
            return {
                       "status": "error",
                       "message": "该手机号码已经被使用"
                   }, 403
        else:
            # 号码未使用, 填入新号码
            connection.Users.find_and_modify(
                {"_id": ObjectId(current_user_id)},
                {
                    "$set": {"cellphone": cellphone}
                }
            )
            new_user = connection.Users.find_one(
                {"_id": ObjectId(current_user_id)})
            return {
                       "status": "ok",
                       "data": new_user,
                       "message": "手机号码更换成功"
                   }, 201


class DeRegister(TokenResource):
    """注销设备(不需要验证手机)"""

    def post(self, cellphone):
        if not verify_phone(cellphone):
            return {
                       'message': '手机手机号码格式错误，请重新输入',
                       "status": "error"
                   }, 403
        current_user_id = self.user_info.user._id
        cursor = connection.Users.find_one(
            {"_id": ObjectId(current_user_id)}
        )
        if not cursor.cellphone:
            return {
                       "status": "error",
                       'message': '您的设备没有绑定手机，不需要注销'
                   }, 403
        if cursor.cellphone != cellphone:
            return {
                       "status": "error",
                       'message': '当前设备关联的手机号码不一致，无法注销'
                   }, 403
        cursor = connection.Devices.find_one(
            {
                "_id": self.user_info.device_id
            }
        )
        if cursor.user_id == cursor.origin_user_id:
            # 该设备为此号码第一台设备, 新建一个用户让其登录,
            # 并为其初始化devices/users信息
            user = connection.Users()
            user.save()
            user_id = user['_id']
            dev = connection.Devices()
            dev['_id'] = self.user_info.device_id
            dev['user_id'] = user_id
            dev['origin_user_id'] = user_id
            dev.save()
            result = connection.Users.find_one({"_id": ObjectId(user_id)})
        else:
            # 不是第一台设备, 把origin_user_id填入user_id
            connection.Devices.find_and_modify(
                {"origin_user_id": cursor.origin_user_id},
                {
                    "$set": {"user_id": cursor.origin_user_id}
                }
            )
            result = connection.Users.find_one(
                {"_id": ObjectId(cursor.origin_user_id)})
        return {
                   "status": "ok",
                   "data": result,
                   "message": "设备注销成功"
               }, 201
