import logging
import random
import re

from bson.objectid import ObjectId
from flask_restful import Resource, reqparse

import top.api
from config import AliConfig
from model import redisdb, connection

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
                       'message': '号码输入有误，请重新输入'
                   }, 400
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
                           "message": "redis服务出错"
                       }, 500
        else:
            return {
                       "status": "error",
                       "message": "短信验证服务出错"
                   }, 500

    def get(self, cellphone):
        """绑定手机号码/更换号码/注销设备
        - op = "bound"  # 绑定
        - op = "change"  # 更换
        - op = "deregister"  # 注销(不需要短信验证)
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            'authorization',
            type=str,
            location='headers'
        )
        parser.add_argument(
            'option',
            type=str,
            required=True,
            help='option not found'
        )
        args = parser.parse_args()
        token = args["authorization"]
        access_token = token[token.find(" ") + 1:]
        if redisdb.exists(
                "oauth:access_token:{}:client_id".format(access_token)
        ):
            device_id = redisdb.get(
                "oauth:access_token:{}:client_id".format(access_token)
            )
        else:
            return {
                       'status': "error",
                       'message': 'Device not found'
                   }, 404
        if not verify_phone(cellphone):
            return {
                       'message': '号码输入有误，请重新输入',
                       "status": "error"
                   }, 400
        # 根据device_id查找对应user_id
        cursor = connection.Devices.find_one({"_id": device_id})
        if cursor:
            current_user_id = cursor.user_id
        else:
            return {'message': 'user_id not found'}, 404
        if args["option"] == "bound":
            # 绑定手机
            cursor = connection.Users.find_one(
                {"cellphone": cellphone}
            )
            if cursor._id == current_user_id:
                return {
                           "status": "error",
                           "message": "你已经绑定过这个号码了"
                       }, 400
            if cursor:
                # 绑定过手机, 将当前设备匹配到先前绑定手机用户
                if current_user_id == cursor._id:
                    # 号码未变, 不做处理
                    return {'message': 'same phone number uploaded'}, 400
                # 把先前绑定手机用户id赋给当前设备
                connection.Devices.find_and_modify(
                    {"_id": device_id},
                    {
                        "$set": {
                            "user_id": cursor._id
                        }
                    }
                )
                return connection.Users.find_one(
                    {"_id": ObjectId(cursor._id)})
            else:
                # 没有绑定过手机, 将cellphone填入当前user_id.cellphone字段
                connection.Users.find_and_modify(
                    {"_id": ObjectId(current_user_id)},
                    {
                        "$set": {"cellphone": cellphone}
                    }
                )
                return connection.Users.find_one(
                    {"_id": ObjectId(current_user_id)})
        elif args["option"] == "change":
            # 更换手机
            cursor = connection.Users.find_one({"cellphone": cellphone})
            if cursor:
                # 号码之前有使用过, 提示该手机号码已被使用
                return {
                           "status": "error",
                           "message": "该手机号码已经被使用"
                       }, 400
            else:
                # 号码未使用, 填入新号码
                connection.Users.find_and_modify(
                    {"_id": ObjectId(current_user_id)},
                    {
                        "$set": {"cellphone": cellphone}
                    }
                )
                return connection.Users.find_one(
                    {"_id": ObjectId(current_user_id)})
        elif args["option"] == "deregister":
            # 注销设备(不需要验证手机)
            cursor = connection.Devices.find_one(
                {
                    "user_id": current_user_id
                }
            )
            if cursor.user_id == cursor.origin_user_id:
                # 该设备为此号码第一台设备, 新建一个用户让其登录,
                # 并为其初始化devices/users信息
                user = connection.Users()
                user.save()
                user_id = user['_id']
                dev = connection.Devices()
                dev['_id'] = device_id
                dev['user_id'] = user_id
                dev['origin_user_id'] = user_id
                dev.save()
                result = connection.Users.find_one({"_id": ObjectId(user_id)})
                return result
            else:
                # 不是第一台设备, 把origin_user_id填入user_id
                connection.Devices.find_and_modify(
                    {"origin_user_id": cursor.origin_user_id},
                    {
                        "$set": {"user_id": cursor.origin_user_id}
                    }
                )
                return connection.Users.find_one(
                    {"_id": ObjectId(cursor.origin_user_id)})
        else:
            return {'message': '不支持的操作'}, 400


class VerifySmsCode(Resource):
    def post(self, cellphone):
        if not verify_phone(cellphone):
            return {
                       'message': '号码输入有误，请重新输入',
                       "status": "error"
                   }, 400
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
                   }, 400
        sys_code = redisdb.lrange("sms_verify:{}".format(cellphone), 0, -1)
        if user_code in sys_code:
            return {
                "status": "ok",
                "message": "验证码匹配正确"
                   }, 201
        else:
            return {
                       "status": "error",
                       "message": "验证码不正确"
                   }, 400
