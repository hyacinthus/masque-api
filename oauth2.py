import logging
from datetime import datetime, timedelta

import bcrypt
from bson.objectid import ObjectId
from flask_oauthlib.provider import OAuth2Provider

from model import Client, Grant, Token, connection
from tasks import logger

log = logging.getLogger("masque.oauth")
oauth = OAuth2Provider()


# 注册认证函数
@oauth.clientgetter
def load_client(client_id):
    """Find client_id in devices, regedit it if not exists"""
    client = Client(client_id)
    return client


@oauth.grantgetter
def load_grant(client_id, code):
    grant = Grant(client_id, code)
    if grant.saved:
        return grant


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant()
    grant.client_id = client_id
    # todo 这里不理解
    grant.code = code['code']
    grant.redirect_uri = request.redirect_uri
    grant.scopes = request.scopes
    grant.user_id = request.user._id
    grant.expires = expires
    grant.save()
    return grant


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        tok = Token(access_token=access_token)
        if tok.saved:
            return tok
    elif refresh_token:
        tok = Token(refresh_token=refresh_token)
        if tok.saved:
            return tok


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)
    tok = Token()
    tok.access_token = token['access_token']
    tok.refresh_token = token['refresh_token']
    tok.client_id = request.client.client_id
    tok.scopes = token['scope']
    tok.user_id = request.user._id
    tok.expires = expires
    tok.save()
    return tok


@oauth.usergetter
def get_user(username, password, *args, **kwargs):
    """username is Device _id, password is crypt _id by
    bcrypt.hashpw in client"""
    _source = username.encode()
    _hashed = password.encode()
    if bcrypt.hashpw(_source, _hashed) != _hashed:
        return None
    device = connection.Devices.find_one({"_id": username})
    if device:
        if device.user_id:
            user = connection.Users.find_one({"_id": ObjectId(device.user_id)})
            # 登录日志
            logger.sign_in_log.delay(device.user_id, device._id)
            if not user:
                log.error("Device user %s is not exists in Users" %
                          device.user_id)
                return None
        # new device, create user
        else:
            user = connection.Users()
            user.save()
            device.user_id = user._id
            device.origin_user_id = user._id
            device.save()
            # 注册日志
            logger.sign_up_log.delay(device.user_id, device._id)
        return user
    else:
        log.error("Create device %s failed." % username)
