from flask import Flask, session
from datetime import timedelta

webapp = Flask(__name__)

from app import user
from app import photo

# set session timeout, user login expires after 1 day
webapp.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

webapp.config['SECRET_KEY'] = 'bf7\xf3MP\xe1\x00}\xaf\xffk5\xeb\xb7\xe7o\xda\x05\x10\xcb\x0b\xff\x03'

# restrict file size to 5 Mb
webapp.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024


