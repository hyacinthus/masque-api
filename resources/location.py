import requests

from functools import reduce
from flask_restful import Resource, reqparse

from model import connection


class SchoolsList(Resource):
    def get(self, lng, lat):
        url_address = 'http://restapi.amap.com/v3/geocode/regeo?key=2f9fd93a6d483072ae4379dd371a2425&' \
                      'location={0},{1}&poitype=141201|141202|141203|141206&' \
                      'extensions=all&batch=true&roadlevel=1'.format(str(lng), str(lat))
        print(url_address)
        url = 'http://restapi.amap.com/v3/place/around?key=2f9fd93a6d483072ae4379dd371a2425&' \
              'location={0},{1}&radius=300&keywords=&types=141201|141202|141203|141206&' \
              'offset=50&page=1&extensions=base'.format(str(lng), str(lat))
        address = requests.get(url_address).json()
        addr = {"name": address["regeocodes"][0]["formatted_address"]}
        try:
            addr["keyword"] = address["regeocodes"][0]["aois"][0]["name"]
        except IndexError:
            addr["keyword"] = None
        get_school = []
        if addr["keyword"] is not None:
            get_school.append(addr["keyword"])
        t = requests.get(url).json()
        for s in t["pois"]:
            get_school.append(s['name'].replace('-', ''))
        result = connection.Schools.find({}, {"name": 1, "_id": 0})
        data = []
        schools = []
        for r in result:
            data.append(r['name'])
        for element in get_school:
            match_list = []
            for i in data:
                if i in element:
                    match_list.append(i)
                else:
                    continue
            if len(match_list) > 0:
                schools.append(match_list[0])
            else:
                pass

        f = lambda x, y: x if y in x else x + [y]
        schools = reduce(f, [[], ] + schools)
        return schools
