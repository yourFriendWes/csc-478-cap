# Installation

Make sure you have Python 3 installed in your local environment

Clone the repo locally

Install required imports `pip install -r requirements.txt`

# Running api locally

Make sure you are in the /app directory when running the following commands

start the application with `FLASK_APP=run.py FLASK_DEBUG=1 flask run`

visit http://localhost:5000 to view sample message

make a post request to http://localhost:5000/registration to register your user. You will need to send a JSON body in the following format:

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
http://localhost:5000/api/location`

# Running and adding tests locally

Tests for new functions can be added in the corresponding test file in `./tests` directory.
For example, if you had a new file called `orange.py` with a function called squeeze() in your `app/api/` path. You would create a new file `tests/api/test_orange.py` The naming of your test file is important for pytest to discover the original test file, and should always follow the `test_original_name_of_file.py` format.

Pytest can be run in a variety of ways, but one way is to run it as a module with the command:
```
python -m pytest tests/
```
