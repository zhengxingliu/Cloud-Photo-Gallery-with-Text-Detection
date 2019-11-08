#!venv/bin/python

from manager_app import manager

#set reloaded to false to prevent flask running twice in debug mode
#prevents autoscaler to be scheduled twice

manager.run(host='0.0.0.0',debug=False, use_reloader=False)
#webapp.run(host='0.0.0.0')
