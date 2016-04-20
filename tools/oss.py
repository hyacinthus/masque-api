import oss2
import json
import bcrypt
import datetime
import http.client
import urllib.parse
from model import redisdb


conn = http.client.HTTPConnection("localhost")


class OssConnection:
    def __init__(self):
        self._bucket = None
        self._extime = None

    # 获得api_token
    def get_api_token(self):
        params = urllib.parse.urlencode({
            'grant_type': 'password',
            'client_id': 'admin',
            'username': 'admin',
            'password': bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode()})
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        conn.request("POST", "/token", params, headers)
        response = conn.getresponse()
        if response.status == 200:
            data = response.read()
            expire_time = json.JSONDecoder().decode(data.decode())['expires_in']
            redisdb.setex('admin:{%s}:api_access_token' % 'admin',
                          expire_time, json.JSONDecoder().decode(data.decode())['access_token'])
            redisdb.set('admin:{%s}:api_refresh_token' % 'admin',
                        json.JSONDecoder().decode(data.decode())['refresh_token'])
        else:
            raise Exception('Status: {0}, Reason: {1}'.format(response.status, response.reason))
        return json.JSONDecoder().decode(data.decode())

    # 获得oss_token
    def get_auth(self):
        access_token = redisdb.get("admin:{admin}:api_access_token")
        access_token = self.get_api_token()['access_token'] if access_token is None else access_token
        headers = {'authorization': "Bearer " + access_token}
        conn.request("GET", "/image_token", headers=headers)
        res = conn.getresponse()
        if res.status == 200:
            data = res.read()
            token = json.JSONDecoder().decode(data.decode())
            if token.get('Credentials'):
                oss_token = token
                _time = token['Credentials']['Expiration']
                self._extime = datetime.datetime.strptime(_time, "%Y-%m-%dT%H:%M:%SZ")
            else:
                raise Exception(token.get('message'))
        else:
            raise Exception('Status: {0}, Reason: {1}'.format(res.status, res.reason))
        auth = oss2.StsAuth(oss_token['Credentials']['AccessKeyId'],
                            oss_token['Credentials']['AccessKeySecret'],
                            oss_token['Credentials']['SecurityToken'])
        return auth

    @property
    def bucket(self):
        if self._bucket is None:
            auth = self.get_auth()
            self._bucket = oss2.Bucket(auth, 'oss-cn-beijing.aliyuncs.com', 'masque')
        elif datetime.datetime.utcnow() > self._extime - datetime.timedelta(minutes=2):
            auth = self.get_auth()
            self._bucket = oss2.Bucket(auth, 'oss-cn-beijing.aliyuncs.com', 'masque')
        else:
            pass
        return self._bucket
