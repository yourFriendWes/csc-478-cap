import os
import psycopg2
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

app = Flask(__name__)
api = Api(app)
load_dotenv()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'some-secret-string'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

db = SQLAlchemy()
db.init_app(app)

from app.api import models, resources, views

@app.before_first_request
def create_tables():
    db.create_all()

app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
jwt = JWTManager(app)

app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return models.RevokedTokenModel.is_jti_blacklisted(jti)


api.add_resource(resources.UserRegistration, '/registration')
api.add_resource(resources.UserLogin, '/login')
api.add_resource(resources.UserLogoutAccess, '/logout/access')
api.add_resource(resources.UserLogoutRefresh, '/logout/refresh')
api.add_resource(resources.TokenRefresh, '/token/refresh')
api.add_resource(resources.AllUsers, '/users')
api.add_resource(resources.WeatherResource, '/weather')
api.add_resource(resources.LocationByIp, '/locationByIp')
api.add_resource(resources.WeatherFiveDayResource, '/fiveday')
api.add_resource(resources.RestaurantResource, '/restaurants')
api.add_resource(resources.EventResource, '/events')
api.add_resource(resources.HotelResource, '/hotels')
api.add_resource(resources.HotelInfoResource, '/hotel')
