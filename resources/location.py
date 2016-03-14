from functools import reduce

import requests
from flask_restful import Resource, reqparse

from model import connection


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
        url_address = 'http://restapi.amap.com/v3/geocode/regeo?key=8734a771f5a4a097a43e96d42f1cc393&' \
                      'location={0},{1}&poitype=141201|141202|141203|141206&' \
                      'extensions=all&batch=true&roadlevel=1'.format(
            args['lon'],
            args['lat'])
        url = 'http://restapi.amap.com/v3/place/around?key=8734a771f5a4a097a43e96d42f1cc393&' \
              'location={0},{1}&radius=300&keywords=&types=141201|141202|141203|141206&' \
              'offset=50&page=1&extensions=base'.format(args['lon'],
                                                        args['lat'])
        address = requests.get(url_address).json()
        addr = {}
        if int(address['status']) == 1:
            try:
                addr["name"] = address["regeocodes"][0]["formatted_address"]
            except IndexError or KeyError:
                addr["name"] = None
            try:
                addr["keyword"] = address["regeocodes"][0]["aois"][0]["name"]
            except IndexError or KeyError:
                addr["keyword"] = None
        else:
            raise Exception(address['info'])
        get_school = []
        if addr["keyword"] is not None:
            get_school.append(addr["keyword"])
        school_name = requests.get(url).json()
        if int(school_name['status']) == 1:
            try:
                pois = school_name["pois"]
            except IndexError or KeyError:
                pois = None
        else:
            raise Exception(school_name['info'])
        if pois is None or pois == []:
            pass
        else:
            for s in pois:
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
