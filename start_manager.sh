#!/bin/bash -ex
cd /home/ubuntu/Desktop/cloud_env
source env/bin/activate
cd /home/ubuntu/Desktop/ece1779_a2/
export FLASK_APP=/home/ubuntu/Desktop/ece1779_a2/run_manager.py
flask run --host 0.0.0.0