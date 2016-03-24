import base64
import hmac
import http.client
import json
import logging
import uuid
from datetime import datetime
from hashlib import sha1
from urllib.parse import quote_plus, urlencode

from flask_restful import Resource, reqparse

from config import AliConfig
from model import redisdb

log = logging.getLogger("masque.image")

if AliConfig:
    access_key_id = AliConfig.IKEY
    access_key_secret = AliConfig.AKEY
    host = AliConfig.HOST
    api_version = AliConfig.API_VERSION


def percent_encode(str):
    res = quote_plus(str)
    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')
    return res


def compute_signature(parameters, access_key_secret):
    sortedParameters = sorted(
        parameters.items(),
        key=lambda parameters: parameters[0]
    )
    canonicalizedQueryString = ''
    for (k, v) in sortedParameters:
        canonicalizedQueryString += '&{}={}'.format(
            percent_encode(k),
            percent_encode(v)
        )
    str2sign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])
    key = "{}&".format(access_key_secret)
    h = hmac.new(
        bytes(key, encoding='utf8'),
        bytes(str2sign, encoding='utf8'),
        sha1
    )
    signature = base64.encodebytes(h.digest()).strip()
    return signature


def compose_url(RoleSessionName):
    utctime = datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')
    parameters = {
        'Format': 'JSON',
        'Version': api_version,
        'AccessKeyId': access_key_id,
        'SignatureVersion': '1.0',
        'SignatureMethod': 'HMAC-SHA1',
        'SignatureNonce': str(uuid.uuid1()),
        'Timestamp': utctime,
        'Action': 'AssumeRole',
        'RoleArn': 'marvint',
        'RoleSessionName': RoleSessionName
    }
    signature = compute_signature(parameters, access_key_secret)
    parameters['Signature'] = signature
    url = "/?{}".format(urlencode(parameters))
    return url


def http_request(site='sts.aliyuncs.com', url=""):
    conn = http.client.HTTPSConnection(site)
    conn.request("GET", url)
    res = conn.getresponse()
    if res:
        data = res.read().decode(encoding='utf-8')
        return json.loads(data), res.status


class GetToken(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            'authorization',
            type=str,
            location='headers'
        )
        args = parser.parse_args()
        token = args["authorization"]
        log.debug(token)
        access_token = token[token.find(" ") + 1:]
        if redisdb.exists(
                "oauth:access_token:{}:client_id".format(access_token)
        ):
            client_id = redisdb.get(
                "oauth:access_token:{}:client_id".format(access_token)
            )
        else:
            return {'message': 'Not found'}, 404
        log.debug(client_id)
        return http_request(host, compose_url(client_id))
