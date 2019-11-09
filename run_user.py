#!venv/bin/python

from app import webapp


webapp.run(host='0.0.0.0',port='5001',debug=False, use_reloader=False)
#webapp.run(host='0.0.0.0')


