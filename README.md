# Installation

Make sure you have Python 3 installed in your local environment

Clone the repo locally

Install required imports `pip install -r requirements.txt`

# Running project locally

`python server.py`

visit http://localhost:5000 to view sample html

visit http://localhost:5000/api/ui/ to view swagger API and interact with endpoints

visit http://localhost:5000/location to view sample api endpoint

Make sample API GET request by opening a second terminal window while the application is running and curling endpoint `curl http://localhost:5000/api/location`

# Running and adding tests locally

Tests for new functions can be added in the corresponding test file in `./tests` directory.
For example, if you had a new file called `orange.py` with a function called squeeze() in your `app/api/` path. You would create a new file `tests/api/test_orange.py` The naming of your test file is important for pytest to discover the original test file, and should always follow the `test_original_name_of_file.py` format.

Pytest can be run in a variety of ways, but one way is to run it as a module with the command:
```
python -m pytest tests/
```
