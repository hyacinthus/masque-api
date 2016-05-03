import logging
from json import dumps

import requests
from flask_restful import reqparse

from config import APIConfig
from model import connection, TokenResource
from tasks import logger

# 需要过滤的黑名单
black_list = ('网络教育', '继续教育', '远程教育', '仙桃学院', '纺织服装学院', '教学部', '分部', '小学')
log = logging.getLogger("masque.location")


def guolv(t):
    """过滤黑名单中关键字"""
    if list(filter(lambda x: True if x in t else False, black_list)):
        return False
    else:
        return True


def rm_duplicates(data=None):
    """列表去重, 保持顺序"""
    data = sorted(data)
    tmp = data[0]
    index = 0
    for i, v in enumerate(data):
        if tmp == v:
            continue
        else:
            data[index] = tmp
            tmp = v
            index += 1
    data[index] = tmp  # 最后一次的tmp值赋给data
    return data[:index + 1]


class SchoolsList(TokenResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('lon',
                            type=str,
                            required=True,
                            help='lon not found!')
        parser.add_argument('lat',
                            type=str,
                            required=True,
                            help='lat not found!')
        parser.add_argument('coordsys',
                            type=str,
                            help='coordinate not found!')
        args = parser.parse_args()
        key = APIConfig.AMAP_AKEY
        if args['coordsys'] == 'gps':
            convert_url = 'http://restapi.amap.com/v3/assistant/coordinate/convert?' \
                          'locations={},{}&' \
                          'coordsys=gps&' \
                          'output=json&' \
                          'key={}'.format(args['lon'], args['lat'], key)
            try:
                convert_location = requests.get(convert_url).json()
            except:
                return {'message': 'Amap API Server No Response!'}, 504

            if not convert_location:
                return {'message': 'Amap API Server No Response!'}, 504
            if convert_location['status'] == "1":
                args['lon'], args['lat'] = convert_location['locations'].split(',')[0],\
                                           convert_location['locations'].split(',')[1]

        regeo_url = 'http://restapi.amap.com/v3/geocode/regeo?' \
                    'key={}&' \
                    'location={},{}&' \
                    'poitype=141201|141202|141203&' \
                    'radius=500&' \
                    'extensions=all&' \
                    'batch=false&' \
                    'roadlevel=1'.format(key, args['lon'], args['lat'])
        try:
            address = requests.get(regeo_url).json()
        except:
            return {'message': 'Amap API Server No Response!'}, 504
        if not address:
            return {'message': 'Amap API Server No Response!'}, 504
        if not address['regeocode']['formatted_address']:
            # 无意义的坐标(如原点或负数坐标)输入高德API并不会报错, 所以需要处理
            return {
                       'status': "error",
                       'message': 'Your coordinate is invalid!'
                   }, 400
        if address['status'] == "1":
            ac = address["regeocode"]["addressComponent"]
            addr = {
                "province": ac["province"],
                "district": ac["district"],
                "city": ac["province"] if not ac["city"] else ac["city"],
                "keyword": address["regeocode"]["aois"][0]["name"] if
                address["regeocode"]["aois"] else None
            }
            pois = address["regeocode"]["pois"]
        else:
            return {'message': 'Amap API Server Error!'}, 500
        get_school = (addr["keyword"],) if addr["keyword"] else ()
        # 获取附近地点
        if pois:
            get_school += tuple(filter(guolv, (i['name'] for i in pois)))
            get_school = tuple(i.replace('-', '') for i in get_school)
        result = connection.Themes.find(
            {"locale.city": "西安市",
             "category": "school"},
            {"full_name": 1, "short_name": 1, "_id": 0}
        )
        data = tuple(item['full_name'] for item in result)
        schools = ()
        for element in get_school:
            match_list = tuple(i for i in data if element.startswith(i) or (
                i[0:2] == "上海" and i.endswith(element)))
            schools += match_list if match_list else ()
        schools = rm_duplicates(schools) if schools else schools
        # 以下为Themes collection初始化处理过程
        # 以"区"结尾返回上一级市,以"县"或"市"结尾直接返回
        if addr["district"].endswith('县') or addr["district"].endswith('市'):
            schools += (addr["district"],)
            cursor = connection.Themes.find_one(
                {
                    "full_name": addr["district"],
                    "category": "district"
                }
            )
            if cursor:
                pass  # 忽略已有
            else:
                doc = connection.Themes()
                doc["category"] = "district"
                doc["short_name"] = addr["district"]
                doc["full_name"] = addr["district"]
                doc["locale"]["province"] = addr["province"]
                doc["locale"]["city"] = addr["city"]
                doc["locale"]["district"] = addr["district"]
                doc.save()  # 新建不存在的主题

        else:
            schools += (addr["city"],)
            cursor = connection.Themes.find_one(
                {
                    "full_name": addr["city"],
                    "category": "city"
                }
            )
            if cursor:
                pass  # 忽略已有
            else:
                doc = connection.Themes()
                doc["category"] = "city"
                doc["short_name"] = addr["city"]
                doc["full_name"] = addr["city"]
                doc["locale"]["province"] = addr["province"]
                doc["locale"]["city"] = addr["city"]
                doc["locale"]["district"] = addr["district"]
                doc.save()  # 新建不存在的主题
        result = list(connection.Themes.find_one(
            {
                "full_name": i,
                "category": {
                    "$nin": ["virtual", "private", "system"]
                }
            }
        ) for i in schools)
        # 位置记录
        loc_log = dumps(
            {
                "user_id": self.user_info.user._id,
                "location": {
                    "coordinates": [float(args['lon']), float(args['lat'])],
                    "type": "Point"
                },
                "schools": result
            }
        )
        logger.geo_request_log.delay(loc_log)
        return {
            'status': 'ok',
            'message': '学校列表筛选完毕',
            'data': result
        }
