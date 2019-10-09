# Running api2 locally

Make sure you are in the /api2 directory when running the following commands

Install required imports `pip install -r api2-requirements.txt`

start the application with `FLASK_APP=run.py FLASK_DEBUG=1 flask run`

visit http://localhost:5000 to view sample message

make a post request to http://localhost:5000/registration to register your user. You will need to send a json body in the following format:

```
{
    "username": "test",
    "password": "test"
}
```

Example cURL request

```
curl -X POST \
  http://localhost:5000/registration \
  -H 'content-type: application/json' \
  -d '{
    "username": "booboo",
    "password": "test"
}'
```

You can view your user and and encoded version of your password by visiting http://localhost:5000/users

request:

```
curl http://localhost:5000/users
```
response:
```
{
    "users": [
        {
            "username": "booboo",
            "password": "$pbkdf2-sha256$29000$2xtDSIkxRsiZc671/t/7Pw$4bfOX0O9wLaD5o8g66thqBqFEdN.2EhPh3XeWYBbRHg"
        }
    ]
}
```
Visit http://localhost:5000/login to login your user and receive an access_token and refresh_token. Use the same body you used to register your user
```
curl -X POST \
  http://localhost:5000/login \
  -H 'content-type: application/json' \
  -d '{
    "username": "boo",
    "password": "test"
}'
```

Visit http://localhost:5000/weather and include the authorization header Authorization Bearer: <your access_token>
```
curl -X GET \
  http://localhost:5000/weather \
  -H 'authorization: Bearer <YOUR TOKEN>'

```
