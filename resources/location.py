import requests
from flask_restful import Resource, reqparse

from config import APIConfig
from model import connection


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


class SchoolsList(Resource):
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
        args = parser.parse_args()
        key = APIConfig.AMAP_AKEY
        regeo_url = 'http://restapi.amap.com/v3/geocode/regeo?' \
                    'key={}&' \
                    'location={},{}&' \
                    'poitype=141201|141202|141203&' \
                    'extensions=all&' \
                    'batch=false&' \
                    'roadlevel=1'.format(key, args['lon'], args['lat'])
        around_url = 'http://restapi.amap.com/v3/place/around?' \
                     'key={}&' \
                     'location={},{}&' \
                     'radius=300&' \
                     'types=141201|141202|141203&' \
                     'extensions=base'.format(key, args['lon'], args['lat'])
        address = requests.get(regeo_url).json()
        if not address:
            return {'message': 'Amap API Server No Response!'}, 504
        if address['status'] == "1":
            ac = address["regeocode"]["addressComponent"]
            addr = {
                "province": ac["province"],
                "district": ac["district"],
                "city": ac["province"] if not ac["city"] else ac["city"],
                "keyword": address["regeocode"]["aois"][0]["name"] if
                address["regeocode"]["aois"] else None
            }
        else:
            return {'message': 'Amap API Server Error!'}, 500
        get_school = (addr["keyword"],) if addr["keyword"] else ()
        # 获取附近地点
        school_name = requests.get(around_url).json()
        if not school_name:
            return {'message': 'Amap API Server No Response!'}, 504
        if school_name['count'] != "0" and school_name['status'] == "1":
            pois = school_name["pois"] if school_name["pois"] else None
        else:
            pois = None
        if pois:
            get_school += tuple(item['name'].replace('-', '') for item in pois)
        result = connection.Schools.find(
            {"city": addr["city"]},
            {"name": 1, "_id": 0}
        )
        data = tuple(item['name'] for item in result)
        schools = ()
        for element in get_school:
            match_list = tuple(i for i in data if element.startswith(i) or (
                i[0:2] == "上海" and i.endswith(element)))
            schools += match_list if match_list else ()
        # 以下为Themes collection初始化处理过程
        if schools:
            schools = rm_duplicates(schools)
            for item in schools:
                cursor = connection.Themes.find_one({"full_name": item})
                if cursor is not None:  # 忽略已有记录
                    continue
                doc = connection.Themes()
                doc["short_name"] = item
                doc["full_name"] = item
                doc["locale"]["province"] = addr["province"]
                doc["locale"]["city"] = addr["city"]
                doc["locale"]["district"] = addr["district"]
                doc.save()  # 新建不存在的主题(学校)
        else:
            # 如果附近没有学校, 返回地区
            schools = (addr["district"],)
            cursor = connection.Themes.find_one({"full_name": addr["district"]})
            if cursor is not None:
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
        result = (connection.Themes.find_one({"full_name": i}) for i in schools)
        return result
