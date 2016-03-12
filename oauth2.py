from datetime import datetime, timedelta
from flask import request
from redis import StrictRedis
from flask_oauthlib.provider import OAuth2Provider
from mongokit import Connection, Document
import logging

from config import MongoConfig, RedisConfig


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("masque.oauth")
oauth = OAuth2Provider()
mongo = Connection(host=MongoConfig.HOST,
                   port=MongoConfig.PORT)
redisdb = StrictRedis(host=RedisConfig.HOST,
                      port=RedisConfig.PORT,
                      db=RedisConfig.DB)


# 认证数据结构
@mongo.register
class User(Document):
    """A user, or resource owner,
    is usually the registered user on your site."""
    __collection__ = 'users'
    __database__ = 'crandom'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        "username": str,
        "password": str,
    }


@mongo.register
class Client(Document):
    """A client is the app which want to use the resource of a user.
    It is suggested that the client is registered by a user on your site,
    but it is not required."""
    __collection__ = 'clients'
    __database__ = 'crandom'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        "client_id": str,
        "client_secret": str,
        "client_type": str,
        "redirect_uris": [str],
        "default_redirect_uri": str,
        "default_scopes": [str],
        "allowed_grant_types": [str],
        "allowed_response_types": [str],
    }


class Grant():
    """A grant token is created in the authorization flow,
    and will be destroyed when the authorization finished.
    new empty grant: Grant()
    get exist grant: Grant(client_id,code)"""
    client_id = None
    code = None
    redirect_uri = None
    scopes = None
    user_id = None
    expires = None
    saved = False

    def __init__(self, client_id=None, code=None):
        if client_id and code:
            if redisdb.exists("oauth:grant:%s:%s:user_id" %
                              (client_id, code)):
                self.client_id = client_id
                self.code = code
                self.redirect_uri = self._get("redirect_uri")
                self.scopes = self._get("scopes")
                self.user_id = self._get("user_id")
                self.expires = self._get("expires")
                self.saved = True

    def _get(self, key):
        return redisdb.get("oauth:grant:%s:%s:%s" % (self.client_id,
                                                     self.code,
                                                     key))

    def _set(self, key, value):
        redisdb.set("oauth:grant:%s:%s:%s" % (self.client_id,
                                              self.code,
                                              key),
                    value)

    def _del(self, key):
        redisdb.delete("oauth:grant:%s:%s:%s" % (self.client_id,
                                                 self.code, key))

    def save(self):
        if self.client_id and self.code:
            self._set("redirect_uri", self.redirect_uri)
            self._set("scopes", self.scopes)
            self._set("user_id", self.user_id)
            self._set("expires", self.expires)
            self.saved = True

    def delete(self):
        if self.client_id and self.code:
            self._del("redirect_uri")
            self._del("scopes")
            self._del("user_id")
            self._del("expires")
            self.saved = False


class Token():
    """ bearer token is the final token
    that could be used by the client.
    new empty token: Token()
    get exist token: Token(access_token)
    get by refresh token: Token(refresh_token=refresh_token)"""
    access_token = None
    refresh_token = None
    client_id = None
    scopes = None
    user_id = None
    expires = None
    saved = False

    def __init__(self, access_token=None, refresh_token=None):
        if access_token:
            if redisdb.exists("oauth:access_token:%s:user_id" %
                              access_token):
                self.access_token = access_token
                self.refresh_token = self._geta("refresh_token")
                self.client_id = self._geta("client_id")
                self.scopes = self._geta("scopes")
                self.user_id = self._geta("user_id")
                self.expires = self._geta("expires")
                self.saved = True
        elif refresh_token:
            if redisdb.exists("oauth:refresh_token:%s:access_token" %
                              refresh_token):
                self.refresh_token = refresh_token
                self.access_token = self._getr("access_token")
                self.client_id = self._getr("client_id")
                self.scopes = self._getr("scopes")
                self.user_id = self._getr("user_id")
                self.expires = self._getr("expires")
                self.saved = True

    def _geta(self, key):
        return redisdb.get("oauth:access_token:%s:%s" %
                           (self.access_token, key))

    def _getr(self, key):
        return redisdb.get("oauth:refresh_token:%s:%s" %
                           (self.refresh_token, key))

    def _dela(self, access_token):
        redisdb.delete("oauth:access_token:%s:%s" %
                       (access_token, self.refresh_token))
        redisdb.delete("oauth:access_token:%s:%s" %
                       (access_token, self.client_id))
        redisdb.delete("oauth:access_token:%s:%s" %
                       (access_token, self.scopes))
        redisdb.delete("oauth:access_token:%s:%s" %
                       (access_token, self.user_id))
        redisdb.delete("oauth:access_token:%s:%s" %
                       (access_token, self.expires))

    def _delr(self, refresh_token):
        redisdb.delete("oauth:refresh_token:%s:%s" %
                       (refresh_token, self.access_token))
        redisdb.delete("oauth:refresh_token:%s:%s" %
                       (refresh_token, self.client_id))
        redisdb.delete("oauth:refresh_token:%s:%s" %
                       (refresh_token, self.scopes))
        redisdb.delete("oauth:refresh_token:%s:%s" %
                       (refresh_token, self.user_id))
        redisdb.delete("oauth:refresh_token:%s:%s" %
                       (refresh_token, self.expires))

    def save(self):
        # one token per one client one user
        old_access = redisdb.get("oauth:user:%s:%s" %
                                 (self.user_id, self.client_id))
        if old_access and old_access != self.access_token:
            old_refresh = redisdb.get(
                "oauth:access_token:%s:refresh_token" %
                old_access)
            if old_refresh:
                self._delr(old_refresh)
            self._dela(old_access)
        # save user index
        if self.client_id and self.user_id:
            redisdb.set("oauth:user:%s:%s" %
                        (self.user_id, self.client_id),
                        self.access_token)
        # save access token
        redisdb.set("oauth:access_token:%s:refresh_token" %
                    self.access_token, self.refresh_token)
        redisdb.set("oauth:access_token:%s:client_id" %
                    self.access_token, self.client_id)
        redisdb.set("oauth:access_token:%s:scopes" %
                    self.access_token, self.scopes)
        redisdb.set("oauth:access_token:%s:user_id" %
                    self.access_token, self.user_id)
        redisdb.set("oauth:access_token:%s:expires" %
                    self.access_token, self.expires)
        # save refresh token
        redisdb.set("oauth:refresh_token:%s:access_token" %
                    self.refresh_token, self.access_token)
        redisdb.set("oauth:refresh_token:%s:client_id" %
                    self.refresh_token, self.client_id)
        redisdb.set("oauth:refresh_token:%s:scopes" %
                    self.refresh_token, self.scopes)
        redisdb.set("oauth:refresh_token:%s:user_id" %
                    self.refresh_token, self.user_id)
        redisdb.set("oauth:refresh_token:%s:expires" %
                    self.refresh_token, self.expires)
        self.saved = True

    def delete(self):
        if self.refresh_token:
            self._delr(self.refresh_token)
        if self.access_token:
            self._dela(self.access_token)
        redisdb.delete("oauth:user:%s:%s" %
                       (self.user_id, self.client_id))
        self.saved = False


# 注册认证函数
@oauth.clientgetter
def load_client(client_id):
    client = mongo.Client.find_one({"client_id": client_id})
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
    user = mongo.User.find_one({"username": username,
                                "password": password})
    return user


# 校验认证部分
class BearerAuth(BasicAuth):
    """ Overrides Eve's built-in basic authorization scheme and uses Redis to
    validate bearer token
    """
    def __init__(self):
        super(BearerAuth, self).__init__()

    def check_auth(self, token, allowed_roles, resource, method):
        """ Check if API request is authorized.
        Examines token in header and checks Redis cache to see if token is
        valid. If so, request is allowed.
        :param token: OAuth 2.0 access token submitted.
        :param allowed_roles: Allowed user roles.
        :param resource: Resource being requested.
        :param method: HTTP method being executed (POST, GET, etc.)
        """
        tok = Token(access_token=token)
        if tok.saved:
            return True

    def authorized(self, allowed_roles, resource, method):
        """ Validates the the current request is allowed to pass through.
        :param allowed_roles: allowed roles for the current request, can be a
                              string or a list of roles.
        :param resource: resource being requested.
        """
        try:
            token = request.headers.get('Authorization').split(' ')[1]
        except:
            token = None
        return self.check_auth(token, allowed_roles, resource, method)
