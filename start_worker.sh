#!/bin/bash -ex
cd /home/ubuntu/Desktop/cloud_env
source env/bin/activate
cd /home/ubuntu/Desktop/ece1779_a2/
/home/ubuntu/Desktop/cloud_env/env/bin/gunicorn --bind 0.0.0.0:5000 --workers=8 app:webapp --access-logfile -
