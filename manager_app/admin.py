from flask import render_template, redirect, url_for, request
from manager_app import manager

import boto3
from app import config
from datetime import datetime, timedelta
from operator import itemgetter

@manager.route('/', methods=['GET'])
@manager.route('/index', methods=['GET'])
def index():
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    # instances = ec2.instances.filter(
    #     Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    instances = ec2.instances.all()



    return render_template("list.html", title="EC2 Instances", instances=instances)



@manager.route('/view_instance/<id>',methods=['GET'])
def view_instance(id):
    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(id)

    client = boto3.client('cloudwatch')

    metric_name = 'CPUUtilization'

    ##    CPUUtilization, NetworkIn, NetworkOut, NetworkPacketsIn,
    #    NetworkPacketsOut, DiskWriteBytes, DiskReadBytes, DiskWriteOps,
    #    DiskReadOps, CPUCreditBalance, CPUCreditUsage, StatusCheckFailed,
    #    StatusCheckFailed_Instance, StatusCheckFailed_System

    namespace = 'AWS/EC2'
    statistic = 'Average'  # could be Sum,Maximum,Minimum,SampleCount,Average

    cpu = client.get_metric_statistics(
        Period=1 * 60,
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,
        Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId', 'Value': id}]
    )

    cpu_stats = []

    for point in cpu['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute / 60
        cpu_stats.append([time, point['Average']])

    cpu_stats = sorted(cpu_stats, key=itemgetter(0))


    return render_template("view_instance.html", title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats)
