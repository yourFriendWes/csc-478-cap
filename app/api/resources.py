from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt_identity, get_raw_jwt,
                                jwt_refresh_token_required, jwt_required)
from flask_restful import Resource, reqparse
from flask import request
from app.api.models import RevokedTokenModel, UserModel

import requests
import time
from os import environ

# Argument Parsers
parser = reqparse.RequestParser()
parser.add_argument('username', help='This field cannot be blank', required=True)   # Requirement 6.1.0
parser.add_argument('password', help='This field cannot be blank', required=True)   # Requirement 6.2.0

zip_parser = reqparse.RequestParser()
zip_parser.add_argument('zipcode', required=False)

# Environment Configuration Variables
open_weather = environ.get('OPEN_WEATHER_KEY')
zomato = environ.get('ZOMATO_KEY')
ticketmaster = environ.get('TICKETMASTER_KEY')
opentrip = environ.get('OPENTRIP_KEY')


class UserRegistration(Resource):
    """
    Requirement 6.0.0: User registers with unique name and password
    """
    def post(self):
        data = parser.parse_args()
        user_name=data['username']

        if not user_name:
            return {'message': 'User name is required'}, 422

        if user_name.isspace():
            return {'message': 'User name cannot be empty space'}, 422

        # Requirements 6.1.1 and 6.1.2: unique username
        if UserModel.find_by_username(user_name):
            return {'message': 'User {} already exists'.format(data['username'])}, 422

        # Requirement 6.2.1: encrypts password
        new_user = UserModel(
            username=data['username'],
            password=UserModel.generate_hash(data['password'])
        )

        # Requirement 6.3.0: stores user in database
        try:
            new_user.save_to_db()
            access_token = create_access_token(identity=data['username'])
            refresh_token = create_refresh_token(identity=data['username'])
            return {
                'message': 'User {} was created'.format(data['username']),
                'access_token': access_token,
                'refresh_token': refresh_token
                }, 200
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogin(Resource):
    """
    Requirement 7.0.0 and 8.0.0: User must login to generate access token
    """
    def post(self):
        data = parser.parse_args()
        current_user = UserModel.find_by_username(data['username'])

        # Requirement 7.1.0: informs user of invalid credentials
        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(data['username'])}, 404

        if UserModel.verify_hash(data['password'], current_user.password):
            access_token = create_access_token(identity=data['username'])
            refresh_token = create_refresh_token(identity=data['username'])

            # Requirement 8.0.0 and 8.2.1: successful login generates access token and refresh token
            return {
                'message': 'Logged in as {}'.format(current_user.username),
                'access_token': access_token,
                'refresh_token': refresh_token
                }
        # Requirement 7.1.0: informs user of invalid credentials
        else:
            return {'message': 'Wrong credentials'}, 401


class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}, 403
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Refresh token has been revoked'}, 403
        except:
            return {'message': 'Something went wrong'}, 500


class AllUsers(Resource):
    def get(self):
        return UserModel.return_all()


class WeatherResource(Resource):
    """
    Requirement 2.0.0: Provides information for local weather
    """
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()

        # Requirement 1.0.0: derives location from IP address
        if data['zipcode'] is None:
            try:
                location = get_location_by_ip()
                zipcode = str(location['zipcode'])
            except:
                return location["error"]
        # Requirement 1.1.0: location zip code is provided by user
        else:
            zipcode = str(data['zipcode'])

        try:
            url = 'http://api.openweathermap.org/data/2.5/weather'
            query_string = {
                'zip': zipcode,
                'units': 'imperial',
                'appid': open_weather
            }
            response = requests.request("GET", url, params=query_string).json()

            time_epoch = response['dt']
            time_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_epoch))

            # Requirement 2.3.0: information returned contains temperature, description, and date
            weather_data = {
                'city': response['name'],
                'date': time_datetime,
                'temperature': response['main']['temp'],
                'description': response['weather'][0]['description']
            }
            return weather_data, 200
        # Requirement 1.2.0: informs user if no information was found
        except:
            return {"error": "No weather information found"}, 404


class WeatherFiveDayResource(Resource):
    """
    Requirement 2.2.0: Provides five day local weather forecast
    """
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()

        # Requirement 1.0.0: derives location from IP address
        if data['zipcode'] is None:
            try:
                location = get_location_by_ip()
                zipcode = str(location['zipcode'])
            except:
                return location["error"]
        # Requirement 1.1.0: location zip code is provided by user
        else:
            zipcode = str(data['zipcode'])

        try:
            url = 'http://api.openweathermap.org/data/2.5/forecast'
            query_string = {
                'zip': zipcode,
                'units': 'imperial',
                'appid': open_weather
            }
            response = requests.request("GET", url, params=query_string).json()

            five_day = []
            for item in response['list']:
                time_epoch = item['dt']
                time_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_epoch))

                # Requirement 2.3.0: information returned contains temperature, description, and date
                details = {
                    'city': response['city']['name'],
                    'time': time_datetime,
                    'temperature': item['main']['temp'],
                    'description': item['weather'][0]['description']
                }
                five_day.append(details)
            return five_day, 200
        # Requirement 1.2.0: informs user if no information was found
        except:
            return{"error": "No weather information found"}, 404


class RestaurantResource(Resource):
    """
    Requirement 3.0.0: Provides information on local restaurants by IP lookup or zip code entry
    """
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()

        # Requirement 1.0.0: derives location from IP address
        if data['zipcode'] is None:
            try:
                location = get_location_by_ip()
                zipcode = str(location['zipcode'])
            except:
                return location["error"]
        # Requirement 1.1.0: location zip code is provided by user
        else:
            zipcode = str(data['zipcode'])

        try:
            # get city from open weather
            city_details = get_city_details(zipcode=zipcode)

            # get zomato's city id
            city_loc_info = self.get_city_id(city_details=city_details)

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

            # Requirement 3.1.0: information contains name, address, phone, price, cuisines, and rating
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
            return restaurant_list, 200
        # Requirement 1.2.0: informs user if no information was found
        except:
            return {"error": "No restaurant information found"}, 404

    # Acquires Zomato API's city ID from lat and long
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
            return city_info, 200
        # Requirement 1.2.0: informs user if no information was found
        except:
            return {"error": "no info from get_city_id()"}, 404


class EventResource(Resource):
    """
    Requirement 4.0.0: Provides information on local events by IP lookup or zip code entry
    """
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()

        # Requirement 1.0.0: derives location from IP address
        if data['zipcode'] is None:
            try:
                location = get_location_by_ip()
                zipcode = str(location['zipcode'])
            except:
                return {"An error was encountered while getting IP location. Please try again, or submit a zipcode"}, 500
        # Requirement 1.1.0: location zip code is provided by user
        else:
            zipcode = str(data['zipcode'])

        try:
            url = 'https://app.ticketmaster.com/discovery/v2/events'
            query_string = {
                'apikey': ticketmaster,
                'postalCode': zipcode
            }

            event_list = []
            response = requests.request("GET", url, params=query_string).json()

            # Requirement 4.1.0: information contains name, address, type, and date
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
        # Requirement 1.2.0: informs user if no information was found
        except:
            return {'error': 'No event information found'}, 404


class HotelResource(Resource):
    """
    Requirement 5.0.0: Provides information on local hotels by IP lookup or zip code entry
    """
    @jwt_required
    def get(self):
        data = zip_parser.parse_args()

        # Requirement 1.0.0: derives location from IP address
        if data['zipcode'] is None:
            try:
                location = get_location_by_ip()
                zipcode = str(location['zipcode'])
            except:
                return location["error"]
        # Requirement 1.1.0: location zip code is provided by user
        else:
            zipcode = str(data['zipcode'])

        try:
            # get city name and lat long from open weather
            city_details = get_city_details(zipcode)

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

            # Requirement 5.1.0: information contains name and rating
            for item in response['features']:
                hotel = {
                    'name': item['properties']['name'],
                    'rating': item['properties']['rate'],
                    'xid': item['properties']['xid']    # xid is unique identifier for an object in open trip map
                }

                hotel_list.append(hotel)

            return hotel_list
        # Requirement 1.2.0: informs user if no information was found
        except:
            return {'error': 'No hotel information found'}, 404


class HotelInfoResource(Resource):
    """
    Requirement 5.0.0: Provides information on a specified hotel
    """
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

            # Requirement 5.1.0: information contains hotel address
            hotel_info = {
                'house_number': response['address']['house_number'],
                'street': response['address']['road'],
                'city': response['address']['city'],
            }

            return hotel_info
        # Requirement 1.2.0: informs user if no information was found
        except:
            return {'error': 'No  hotel information found'}, 404


class TokenRefresh(Resource):
    """
    Requirement 8.2.1: Refresh token generates a new access token
    """
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return {'access_token': access_token}


# Get city name, lat, and long from Open Weather API
def get_city_details(zipcode):
    url = 'http://api.openweathermap.org/data/2.5/weather'
    query_string = {
        'zip': zipcode,
        'units': 'imperial',
        'appid': open_weather
    }
    try:
        response = requests.request("GET", url, params=query_string).json()
        city_details = {
            'city': response['name'],
            'lat': response['coord']['lat'],
            'lon': response['coord']['lon']
        }
        return city_details
    # Requirement 1.2.0: informs user if no information was found
    except:
        return {"error": "no info from get_city_details"}, 404


def get_location_by_ip():
    """
    Requirement 1.0.0: Find location by user IP address
    """
    try:
        ip_address = ''
        if 'HTTP_X_FORWARDED_FOR' in request.environ:
            ip_addrs = request.environ['HTTP_X_FORWARDED_FOR'].split(',')
            ip_address = ip_addrs[len(ip_addrs)-1]
        else:
            ip_address = request.remote_addr
        response = requests.get("http://ip-api.com/json/{}".format(ip_address))
        js = response.json()
        location = {
            'ipaddr': js['query'],
            'city': js['city'],
            'country': js['country'],
            'zipcode': js['zip']
        }
        return location
    # Requirement 1.2.0: informs user if no information was found
    except Exception as e:
        return {
            "error": "unknown location for IP: {0}".format(request.remote_addr)
        }
