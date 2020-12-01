# MoSoon Massage Backend

This is the backend server of project MoSoon Massage, build with Python Django.

## Steps to Start Development

1. Clone this repo.
2. `python3 -m venv env` Create a virtual env
3. `pip3 install -r requirements.txt` Install packages
4. Add `config.py` in project directory.
5. Insert the config content into `config.py` according to the structure below.
6. `python3 manage.py runserver 8080` Start dev server at http://localhost:8080

## Config Structure

```python
# ./config.py

config = {
    "HOST_NAME": "",
    "SECRET_KEY": '',
    "MONGODB_NAME": "",
    "MONGODB_CONNECT_STRING": "",
    "MPG_GATEWAY": "",
    "HASH_KEY": "",
    "HASH_IV": "",
    "MERCHANT_ID": "",
    "AWS_ACCESS_KEY": '',
    "AWS_SECRET_KEY": ''
}
```
