ami_id = 'ami-0edd349028e306dd0'
instance_type = 't2.small'
security_group = ['ece1779']
key_name = 'ece_1779'


userdata = """#cloud-config

runcmd:
- exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
- echo BEGIN
- date '+%Y-%m-%d %H:%M:%S'
- cd /home/ubuntu/Desktop/ece1779_a2
- sudo chmod 777 error.log
- sudo chmod 777 access.log
- ./start_worker.sh
- echo END
"""


