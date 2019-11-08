from app import webapp
import boto3
import urllib.request
from apscheduler.schedulers.background import BackgroundScheduler
import time, atexit

httpRate = 0

@webapp.before_request
def updata_http_rate():
    global httpRate
    httpRate += 1
    print('increment http request rate to', httpRate)


def put_http_rate():
    global httpRate
    instanceID = get_instance_id()
    #instanceID = str('test')

    client = boto3.client('cloudwatch')
    response = client.put_metric_data(
        Namespace='Custom',
        MetricData=[
            {
                'MetricName': 'HttpRequestRate',
                'Dimensions': [
                    {
                        'Name': 'InstanceID',
                        'Value': instanceID
                    },
                ],
                'Unit':'Count',
                'Value': httpRate
            },
        ],
    )

    print("updated http request rate to cloudwatch")
    httpRate = 0


# periodically run these tasks
scheduler = BackgroundScheduler()
job = scheduler.add_job(put_http_rate, 'interval', seconds=30, id='http_metric')
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


def get_instance_id():
    instanceid = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read().decode()
    return instanceid