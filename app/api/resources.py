from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt_identity, get_raw_jwt,
                                jwt_refresh_token_required, jwt_required)
from flask_restful import Resource, reqparse
from app.api.models import RevokedTokenModel, UserModel

import requests
import time
from os import environ

parser = reqparse.RequestParser()
parser.add_argument('username', help = 'This field cannot be blank', required = True)
parser.add_argument('password', help = 'This field cannot be blank', required = True)

zip_parser = reqparse.RequestParser()
zip_parser.add_argument('zipcode', help = 'This field cannot be blank', required = False)

# Config variables
open_weather = environ.get('OPEN_WEATHER_KEY')


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

            weather_data = {
                'city': r['name'],
                'temperature': r['main']['temp'],
                'description': r['weather'][0]['description']
            }
            weather_message = f"{weather_data['temperature']:.1f} degrees and {weather_data['description']}"

            return {
                weather_data['city']: weather_message
            }
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

            # returns a list of weather information for every 3 hours for the next five days

            five_day = {}
            index = 0
            for item in r['list']:
                day = "Item " + str(index + 1)

                time_epoch = r['list'][index]['dt']
                time_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_epoch))

                temp = r['list'][index]['main']['temp']

                details = {
                    'time': time_datetime,
                    'temperature': f'{temp:.1f} degrees',
                    'description': r['list'][index]['weather'][0]['description']
                }
                five_day[day] = details
                index += 1

            return five_day

        except:
            return{
                "error": "no information"
            }


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity = current_user)
        return {'access_token': access_token}
