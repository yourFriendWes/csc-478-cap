from flask import jsonify

from app.run import app


# @app.route('/')
def index():
    return jsonify({'message': "Let's try to travel with our experimental API"})
