from flask import Flask


manager = Flask(__name__)

from manager_app import admin, config, ec2, http_rate

manager.config['SECRET_KEY'] = '\x8b\xc1\xc7\xa0\xa9Q\xdc\x90\xb4\x1d\xed\x86\xa4\xf8\x07\t\xefG\x92\r\x9b\x93f\x11'