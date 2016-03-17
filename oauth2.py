from datetime import datetime, timedelta
from flask_oauthlib.provider import OAuth2Provider
import logging
import bcrypt

from model import Client, Grant, Token, connection

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("masque.oauth")
oauth = OAuth2Provider()


# 注册认证函数
@oauth.clientgetter
def load_client(client_id):
    client = Client(client_id)
    if client.client_id:
        return client
    else:
        return None


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
    """username is Users _id, password is crypt _id by
    bcrypt.hashpw in client"""
    user = connection.User.find_one({"_id": username})
    if user and bcrypt.hashpw(username, password) == password:
        return user
