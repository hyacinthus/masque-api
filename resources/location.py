import requests
from flask_restful import Resource, reqparse

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
        regeo_url = 'http://restapi.amap.com/v3/geocode/regeo?' \
                    'key=ab158f36829f810346ef3526727f1aa4&' \
                    'location={0},{1}&' \
                    'poitype=141201|141202|141203&' \
                    'extensions=all&' \
                    'batch=false&' \
                    'roadlevel=1'.format(args['lon'], args['lat'])
        around_url = 'http://restapi.amap.com/v3/place/around?' \
                     'key=ab158f36829f810346ef3526727f1aa4&' \
                     'location={0},{1}&' \
                     'radius=300&' \
                     'keywords=&' \
                     'types=141201|141202|141203&' \
                     'offset=50&' \
                     'page=1&' \
                     'extensions=base'.format(args['lon'], args['lat'])
        address = requests.get(regeo_url).json()
        addr = {}
        if address['status'] == "1":
            for element in ["province", "city", "district"]:
                try:
                    addr[element] = address["regeocode"]["addressComponent"][
                        element]
                except IndexError or KeyError:
                    addr[element] = []
            try:
                addr["keyword"] = address["regeocode"]["aois"][0]["name"]
            except IndexError or KeyError:
                addr["keyword"] = None
            if addr['city'] == []:  # 直辖市会有city为空list的情况,用省填充
                addr['city'] = addr['province']
        else:
            raise Exception(address['info'])
        get_school = []
        if addr["keyword"] is not None:
            get_school.append(addr["keyword"])
        school_name = requests.get(around_url).json()

        if school_name['status'] == "1":
            try:
                pois = school_name["pois"]
            except IndexError or KeyError:
                pois = None
        else:
            raise Exception(school_name['info'])
        if pois == [] or pois is None:
            pass
        else:
            for s in pois:
                get_school.append(s['name'].replace('-', ''))
        result = connection.Schools.find(
            {"city": addr["city"]},
            {"name": 1, "_id": 0}
        )
        data = []
        schools = []
        for element in result:
            data.append(element['name'])
        for element in get_school:
            match_list = []
            for i in data:
                if element.startswith(i) or (
                            i.endswith(element) and i[0:2] == "上海"):
                    match_list.append(i)
                else:
                    continue
            if len(match_list) > 0:
                schools.append(match_list[0])
            else:
                pass

        # 以下为Themes collection初始化处理过程
        if len(schools) != 0:
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
            schools.append(addr["district"])
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
        result = map(lambda i: connection.Themes.find_one({"full_name": i}),
                     schools)
        return result
