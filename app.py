from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder
from OSMPythonTools.overpass import Overpass
import pandas as pd
import numpy as np
import osm2geojson
import overpy
from geopy.geocoders import Nominatim as Nominatims
import json

app = Flask(__name__)
api = Api(app)



class Ping(Resource):
    def get(self):
        return {'response': 'pong'}


api.add_resource(Ping, '/ping')

class Scraper(Resource):
    def get(self) :

        parser = reqparse.RequestParser()
        parser.add_argument('zone_code', type= str,  help='missing zone code', required = False, location = 'args')
        parser.add_argument('poi_name', type = str, location = 'args')
        parser.add_argument('shop_category', type = str, location = 'args')
        parser.add_argument('amenity_category', type = str, location = 'args')
        args = parser.parse_args()

        zone_code = args['zone_code']
        poi_name = args['poi_name']
        print(args)
        try : shop_category = args['shop_category']
        except TypeError :
            shop_category = None
        try :amenity_category = args['amenity_category']
        except TypeError :
            shop_category = None

        target = []
        
        if poi_name != None :
            target.append(str('"name"~"' + poi_name + '"'))
        if shop_category != None :
            target.append('"shop"="' + shop_category + '"')
        if amenity_category != None :
            target.append('"amenity"="' + amenity_category + '"')
  
        nominatim = Nominatim()
        zone = nominatim.query(zone_code) 

        shop_query = overpassQueryBuilder(area = zone, 
                                        elementType = ['node','way','relation'], 
                                        selector = target, 
                                        out ='body'
                                        )
        overpass = Overpass()
        shops = overpass.query(shop_query, timeout = 60)

        shop_df = pd.DataFrame()
        shops_list = shops.elements()
        
        shop_df['name'] = [shop.tag('name') for shop in shops_list]

        address = []

        for shop in shops_list :
            try :
                address.append( shop.tag('addr:housenumber') + ' ' + 
                                shop.tag('addr:street') + ' ' +
                                shop.tag('addr:city') + ' ' +
                                shop.tag('addr:postcode')
                            ) 
                                
            except TypeError :
                address.append(None)

        shop_df['address'] = address
                        
        lat =[]
        lon =[]

        for shop in shops_list :
            if shop.type() == 'node' :
                lat.append(shop.lat())
                lon.append(shop.lon())
            elif shop.type() == 'way':
                lat.append(shop.nodes()[0].lat())
                lon.append(shop.nodes()[0].lon())
            elif shop.members()[0].type() == 'node':
                lat.append(shop.members()[0].lat())
                lon.append(shop.members()[0].lon())
            elif shop.members()[0].type() == 'way' and shop.members()[0].nodes() != []:
                lat.append(shop.members()[0].nodes()[0].lat())
                lon.append(shop.members()[0].nodes()[0].lon())
            else :
                lat.append(None)
                lon.append(None)

        shop_df['lat'] = lat
        shop_df['lon'] = lon

        shop_df['lat'] = shop_df["lat"].apply(lambda x : float(x))
        shop_df['lon'] = shop_df["lon"].apply(lambda x : float(x))

        for index, row in shop_df.iterrows() :
            if shop_df.at[index,'address'] == None :
                try :
                    shop_df.at[index,'address'] = str(Nominatims(user_agent = 'reverse_geocode').reverse((shop_df.at[index,'lat'],shop_df.at[index,'lon']), 
                                                                                                    timeout = None
                                                                                                )
                    )
                except ValueError:
                    shop_df.at[index,'address'] = None
        return json.loads(shop_df.to_json(orient = 'records'))  

api.add_resource(Scraper,
                  '/Scraper',
                  )

if __name__ == '__main__':
    app.run(debug=False)

