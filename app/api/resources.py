from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt_identity, get_raw_jwt,
                                jwt_refresh_token_required, jwt_required)
from flask_restful import Resource, reqparse
from flask import request
from app.api.models import RevokedTokenModel, UserModel

import requests
import time
from os import environ

parser = reqparse.RequestParser()
parser.add_argument('username', help = 'This field cannot be blank', required = True)
parser.add_argument('password', help = 'This field cannot be blank', required = True)

zip_parser = reqparse.RequestParser()
zip_parser.add_argument('zipcode', required = False)

# Config variables
open_weather = environ.get('OPEN_WEATHER_KEY')
zomato = environ.get('ZOMATO_KEY')
ticketmaster = environ.get('TICKETMASTER_KEY')
opentrip = environ.get('OPENTRIP_KEY')


class UserRegistration(Resource):
    def post(self):
        data = parser.parse_args()

        if UserModel.find_by_username(data['username']):
            return {'message': 'User {} already exists'.format(data['username'])}

        new_user = UserModel(
            username = data['username'],
            password = UserModel.generate_hash(data['password'])
        )

        try:
            new_user.save_to_db()
            access_token = create_access_token(identity = data['username'])
            refresh_token = create_refresh_token(identity = data['username'])
            return {
                'message': 'User {} was created'.format(data['username']),
                'access_token': access_token,
                'refresh_token': refresh_token
                }
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogin(Resource):
    def post(self):
        data = parser.parse_args()
        current_user = UserModel.find_by_username(data['username'])

        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(data['username'])}

        if UserModel.verify_hash(data['password'], current_user.password):
            access_token = create_access_token(identity = data['username'])
            refresh_token = create_refresh_token(identity = data['username'])
            return {
                'message': 'Logged in as {}'.format(current_user.username),
                'access_token': access_token,
                'refresh_token': refresh_token
                }
        else:
            return {'message': 'Wrong credentials'}


class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti = jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti = jti)
            revoked_token.add()
            return {'message': 'Refresh token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class TokenRefresh(Resource):
    def post(self):
        return {'message': 'Token refresh'}


class AllUsers(Resource):
    def get(self):
        return UserModel.return_all()

    def delete(self):
        return UserModel.delete_all()


class WeatherResource(Resource):
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()

        try:
            zipcode = data['zipcode']
            url = 'http://api.openweathermap.org/data/2.5/weather?zip={}&units=imperial&appid={}'
            r = requests.get(url.format(zipcode, open_weather)).json()

            time_epoch = r['dt']
            time_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_epoch))

            weather_data = {
                'city': r['name'],
                'date': time_datetime,
                'temperature': r['main']['temp'],
                'description': r['weather'][0]['description']
            }
            return weather_data

        except:
            return {
                "error": "no information"
            }


class WeatherFiveDay(Resource):
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()

        try:
            zipcode = data['zipcode']
            url = 'http://api.openweathermap.org/data/2.5/forecast?zip={}&units=imperial&appid={}'
            r = requests.get(url.format(zipcode, open_weather)).json()

            five_day = []
            for item in r['list']:
                time_epoch = item['dt']
                time_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_epoch))

                details = {
                    'city': r['city']['name'],
                    'time': time_datetime,
                    'temperature': item['main']['temp'],
                    'description': item['weather'][0]['description']
                }
                five_day.append(details)
            return five_day

        except:
            return{
                "error": "no information"
            }
          

# class LocationByIp(Resource):
#     @jwt_required
#     def get(self):
#         try:
#             ip_address = request.remote_addr
#             response = requests.get("http://ip-api.com/json/{}".format(ip_address))
#             js = response.json()
#             location['city'] = js['city']
#             location['country'] = js['country']
#             location['zipcode'] = js['zip']
#             return location
#         except Exception as e:
#             return 'Unknown location'

class RestaurantResource(Resource):
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()
        zipcode = data['zipcode']

        # get city from open weather
        city_details = get_city_details(zipcode=zipcode)

        # get zomato's city id
        city_loc_info = self.get_city_id(city_details=city_details)

        try:
            # get list of restaurants from zomato with city id
            url = 'https://developers.zomato.com/api/v2.1/search'
            query_string = {
                'entity_id': city_loc_info['city_id'],
                'entity_type': city_loc_info['type']
            }
            headers = {
                'user-key': zomato
            }
            response = requests.request("GET", url, headers=headers, params=query_string).json()

            restaurant_list = []

            for item in response['restaurants']:
                restaurant = {
                    'name': item['restaurant']['name'],
                    'address': item['restaurant']['location']['address'],
                    'phone': item['restaurant']['phone_numbers'],
                    'cuisine': item['restaurant']['cuisines'],
                    'price_scale': item['restaurant']['price_range'],
                    'rating': item['restaurant']['user_rating']['aggregate_rating']
                }
                restaurant_list.append(restaurant)
            return restaurant_list

        except:
            return {"error": "no info from restaurant resource"}

    def get_city_id(self, city_details):
        url = 'https://developers.zomato.com/api/v2.1/locations'
        querystring = {
            'query': city_details['city'],
            'lat': city_details['lat'],
            'lon': city_details['lon']
        }
        headers = {
            'user-key': zomato
        }
        try:
            response = requests.request("GET", url, headers=headers, params=querystring).json()

            city_info = {
                'city_id': response['location_suggestions'][0]['entity_id'],
                'type': response['location_suggestions'][0]['entity_type']
            }
            return city_info
        except:
            return {"error": "no info from get_city_id"}


class EventResource(Resource):
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()
        zipcode = data['zipcode']

        try:
            url = 'https://app.ticketmaster.com/discovery/v2/events'
            query_string = {
                'apikey': ticketmaster,
                'postalCode': zipcode
            }

            event_list = []
            response = requests.request("GET", url, params=query_string).json()
            for item in response['_embedded']['events']:
                classifications = []

                for classification in item['classifications']:
                    class_type = classification['segment']['name']
                    genre = classification['genre']['name']
                    subgenre = classification['subGenre']['name']

                classifications.append(class_type)
                classifications.append(genre)
                classifications.append(subgenre)

                event = {
                    'name': item['name'],
                    'date': item['dates']['start']['localDate'],
                    'classifications': classifications,
                    'venue': item['_embedded']['venues'][0]['name'],
                    'address': item['_embedded']['venues'][0]['address']['line1']
                }
                event_list.append(event)
            return event_list

        except:
            return {'error': 'no info found'}


class HotelResource(Resource):
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()
        zipcode = data['zipcode']

        # get city name and lat long from open weather
        city_details = get_city_details(zipcode)

        try:
            url = 'https://api.opentripmap.com/0.1/en/places/radius'
            query_string = {
                # 15 miles is 24140 meters
                'radius': 24140,
                'lon': city_details['lon'],
                'lat': city_details['lat'],
                'kinds': 'accomodations',
                'apikey': opentrip
            }
            hotel_list = []
            response = requests.request("GET", url, params=query_string).json()

            for item in response['features']:
                hotel = {
                    'name': item['properties']['name'],
                    'rating': item['properties']['rate'],
                    # xid is unique identifier for an object in open trip map
                    'xid': item['properties']['xid']
                }

                hotel_list.append(hotel)

            return hotel_list
        except:
            return {'error': 'no info found'}


class HotelInfo(Resource):
    @jwt_required
    def get(self):
        hotel_id_parser = reqparse.RequestParser()
        hotel_id_parser.add_argument('xid', help='This field cannot be blank', required=True)

        data = hotel_id_parser.parse_args()
        hotel_id = data['xid']

        try:
            url = f"https://api.opentripmap.com/0.1/en/places/xid/{hotel_id}"
            query_string = {
                'apikey': opentrip
            }
            response = requests.request("GET", url, params=query_string).json()
            hotel_info = {
                'house_number': response['address']['house_number'],
                'street': response['address']['road'],
                'city': response['address']['city'],
            }

            return hotel_info
        except:
            return {'error': 'no info'}


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity = current_user)
        return {'access_token': access_token}


def get_city_details(zipcode):
    url = 'http://api.openweathermap.org/data/2.5/weather?zip={}&units=imperial&appid={}'
    try:
        r = requests.get(url.format(zipcode, open_weather)).json()
        city_details = {
            'city': r['name'],
            'lat': r['coord']['lat'],
            'lon': r['coord']['lon']
        }
        return city_details
    except:
        return {"error": "no info from get_city_details"}
