import boto3,random, mysql.connector
from datetime import datetime, timedelta
from operator import itemgetter


def get_http_rate():

    client = boto3.client('cloudwatch')

    metric_name = 'AllRequests'


    namespace = 'AWS/S3'
    statistic = 'Sum'  # could be Sum,Maximum,Minimum,SampleCount,Average

    http = client.get_metric_statistics(
        Period=1 * 60,
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,
        Unit='Counts',
        Statistics=[statistic],
        Dimensions=[{'Name': 'Http Request', 'Value': 'Counts'}]
    )

    http_rate = []

    for point in http['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute / 60
        http_rate.append([time, point['Sum']])

    http_rate = sorted(http_rate, key=itemgetter(0))


    return http_rate

