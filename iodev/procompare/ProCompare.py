__author__ = 'Todd Berk'
import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from urllib import parse
from datetime import datetime

from ..pushlog.GPS import Point

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

MAPBOX_TOKEN = 'pk.eyJ1IjoidG9kZHB1c2giLCJhIjoiY2llc3o3Zzd6MDBncW5nbTAzc3hnY2g3bCJ9.cy8CYPPAEnCWWoF4CSHFZQ'

PROCOMPARE_MAP_ID = 'toddpush.ciesz7fts00illxm38o3l1rmo'

class ProCompareMap(object):
    latitude = 0
    longitude = 0
    zoom = 19
    image_width = 700
    image_height = 425
    format = 'jpg90'


class ProCompare(object):

    def __init__(self, segment_points, name, session_name):

        #Get average/center of segment points
        avg_segment_point = self.get_point_list_average(segment_points)

        # Create Map, centered on average of segment_points
        map = ProCompareMap()
        map.latitude = avg_segment_point.latitude_deg
        map.longitude = avg_segment_point.longitude_deg

        # Convert to GeoJSON
        geojson = self.point_list_to_geojson(segment_points)

        # Get image from MapBox
        image = self.get_static_map_image(map, geojson)

        im_rgba = self.overlay_trackday_logo(image)

        out = self.overlay_name_date_session(im_rgba, name, datetime.now(), session_string=session_name)

        self.image = out

    @staticmethod
    def overlay_trackday_logo(image):
        # Create RGBA Version for doing image manipulations
        im_rgba = image.convert('RGBA')

        # Overlay PUSH Logo
        push_logo = Image.open(__location__+"/PUSHLogo.png")
        im_rgba.paste(push_logo, (485, 25), push_logo)
        return im_rgba

    @staticmethod
    def overlay_name_date_session(image, name, date, session_string=None):
        # Create RGBA Version for doing image manipulations
        image = image.convert('RGBA')
        # make a blank image for the text, initialized to transparent text color
        txt = Image.new('RGBA', image.size, (255, 255, 255, 0))

        # get a font ProximaNovaExCn-Bold
        font_lrg = ImageFont.truetype(__location__+'/ProximaNova-Light.ttf', 40)
        font_lrg_bold = ImageFont.truetype(__location__+'/ProximaNovaExCn-Bold.ttf', 40)
        font_med = ImageFont.truetype(__location__+'/ProximaNova-Light.ttf', 32)
        font_sml = ImageFont.truetype(__location__+'/ProximaNova-Light.ttf', 28)

        # get a drawing context
        d = ImageDraw.Draw(txt)

        date_string = datetime.strftime(date, '%b %d %Y')

        # draw strings
        d.text((10, 300), name, font=font_lrg_bold, fill=(255, 255, 255, 255))
        if session_string:
            d.text((10, 345), session_string, font=font_med, fill=(255, 255, 255, 255))
            d.text((10, 380), date_string, font=font_sml, fill=(255, 255, 255, 255))

        out = Image.alpha_composite(image, txt)

        return out

    @staticmethod
    def get_static_map_image( map, geojson=None):
        if geojson:
            mapbox_request = 'https://api.mapbox.com/v4/{mapid}/geojson({geojson})/{m.longitude},{m.latitude},{m.zoom}/' \
                             '{m.image_width}x{m.image_height}.{m.format}?access_token={token}'
        else:
            mapbox_request = 'https://api.mapbox.com/v4/{mapid}/{m.longitude},{m.latitude},{m.zoom}/' \
                             '{m.image_width}x{m.image_height}.{m.format}?access_token={token}'
        mapbox_request = mapbox_request.format(m=map, geojson=parse.quote(geojson),
                                               mapid=PROCOMPARE_MAP_ID, token=MAPBOX_TOKEN)

        r = requests.get(mapbox_request)
        image = Image.open(BytesIO(r.content))
        return image

    @staticmethod
    def point_list_to_geojson(point_list, properties=None):
        import json
        # points dict
        coordinates = []
        for point in point_list:
            coordinates.append([round(point.longitude_deg, 8), round(point.latitude_deg, 8)])

        # Create GeoJSON
        json_dict = {"type": "Feature"}
        if properties is None:
            json_dict["properties"] = {"stroke": "#f44", "stroke-opacity": 0.9, "stoke-width": 6}
        else:
            json_dict["properties"] = properties["properties"]
        json_dict["geometry"] = {"type": "LineString", "coordinates": coordinates}

        geojson = json.dumps(json_dict)

        return geojson

    @staticmethod
    def get_point_list_average(point_list):
        lat_sum = 0
        lon_sum = 0

        for index, point in enumerate(point_list, start=1):
            lat_sum += point.latitude_deg
            lon_sum += point.longitude_deg

        lat_avg = lat_sum / index
        lon_avg = lon_sum / index

        return Point(lat_avg, lon_avg)
