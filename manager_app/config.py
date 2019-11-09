db_config = {'user': 'admin',
             'password': 'ece1779pass',
             'host': 'ece1779a2-db.cguvohxj73qh.us-east-1.rds.amazonaws.com',
             'database': 'ece1779_a2'}


s3_config = {"bucket": "1779a2"}

ami_id = 'ami-028e4edc85fcac1f8'
instance_type = 't2.small'
security_group = ['ece1779']
key_name = 'ece_1779'

ARN = 'a2loadbalancer-1794919167.us-east-1.elb.amazonaws.com'


# use user data to pass on bash script to start worker automatically
userdata = """#!/bin/bash
cd /home/ubuntu/Desktop/ece1779_a2
./start.sh &
 """



# #!/bin/bash -ex
# cd /home/ubuntu/Desktop/cloud_env
# source env/bin/activate
# cd /home/ubuntu/Desktop/ece1779_a2/
# /home/ubuntu/Desktop/cloud_env/env/bin/gunicorn --bind 0.0.0.0:5000 --workers=8 app:webapp --access-logfile -
# date '+%Y-%m-%d %H:%M:%S'




# userdata = """#!/bin/bash
# echo CP1
# cd /home/ubuntu/Desktop/ece1779_a2
# echo CP2
# ./start.sh &
# echo CP3
# touch /tmp/cp3-1
#  """

