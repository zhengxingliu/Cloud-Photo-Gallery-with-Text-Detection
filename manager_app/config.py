db_config = {'user': 'admin',
             'password': 'ece1779pass',
             'host': 'ece1779a2-db.cguvohxj73qh.us-east-1.rds.amazonaws.com',
             'database': 'ece1779_a2'}


s3_config = {"bucket": "1779a2"}

ami_id = 'ami-0bf7c16df888353f8'
instance_type = 't2.small'
security_group = ['ece1779']
key_name = 'ece_1779'


userdata = """#!/bin/bash
echo CP1
cd /home/ubuntu/Desktop/ece1779_a2
echo CP2
./start.sh &
echo CP3
touch /tmp/cp3-1
 """


# #!/bin/bash -ex
# cd /home/ubuntu/Desktop/cloud_env
# source env/bin/activate
# cd /home/ubuntu/Desktop/ece1779_a2/
# /home/ubuntu/Desktop/cloud_env/env/bin/gunicorn --bind 0.0.0.0:5000 --workers=8 app:webapp --access-logfile -
# date '+%Y-%m-%d %H:%M:%S'

# userdata = """#cloud-config
#
# runcmd:
# - [ exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1 ]
# - echo BEGIN
# - [ cd /home/ubuntu/Desktop/ece1779_a2 ]
# - source venv/bin/activate
# - [ /home/ubuntu/Desktop/ece1779/aws/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers=1 app:webapp ]
# - echo END
#
# """
#


