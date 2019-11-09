import boto3
from datetime import datetime, timedelta
from operator import itemgetter

# retrieve custom http request rate metric from cloudwatch
def get_http_rate(id):

    client = boto3.client('cloudwatch')

    instanceID = str(id)
    metric_name = 'HttpRequestRate'


    rate = client.get_metric_statistics(
        Period=1 * 60,
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace='Custom',
        Unit='Count',
        Statistics=['Sum'],
        Dimensions=[{'Name': 'InstanceID','Value': instanceID}]
    )

    http_rate = []

    for point in rate['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute / 60
        http_rate.append([time, point['Sum']])

    http_rate = sorted(http_rate, key=itemgetter(0))


    return http_rate


