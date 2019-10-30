from flask import render_template, redirect, url_for, request, flash
from manager_app import manager, config

import boto3,random
from datetime import datetime, timedelta
from operator import itemgetter

@manager.route('/', methods=['GET'])
@manager.route('/index', methods=['GET'])
def index():
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    # instances = ec2.instances.all()

    # instances = ec2.instances.filter(
    #     Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    instances = ec2.instances.filter(
        Filters=[{'Name': 'tag-value', 'Values': ['ece1779_a2_user']},
                  {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    size = len(list(instances))

    return render_template("index.html", title="EC2 Instances", instances=instances, size=size)



@manager.route('/view_instance/<id>',methods=['GET'])
# view CPU and request info of selected instance
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






@manager.route('/create', methods=['POST'])
def ec2_create():
    create_instances(1)
    flash('New worker created')
    return redirect(url_for('index'))


def create_instances(num_create):
    ec2 = boto3.resource('ec2')
    instances = ec2.create_instances(ImageId=config.ami_id,
                                     InstanceType=config.instance_type,
                                     SecurityGroups=config.security_group,
                                     KeyName=config.key_name,
                                     UserData=config.userdata,
                                     Monitoring={'Enabled': True},
                                     MinCount=1,
                                     MaxCount=num_create)
    id_list = []
    for ins in instances:
        id_list.append(ins.id)
    ec2.create_tags(Resources=id_list, Tags=[{'Key': 'name', 'Value': 'ece1779_a2_user'}])



@manager.route('/destroy', methods=['POST'])
def ec2_destroy():
    if destroy_instances(1):
        flash('Worker destroyed')
        return redirect(url_for('index'))
    else:
        flash ('No worker can be further destroyed')
        return redirect(url_for('index'))




def destroy_instances(num_destroy):
    ec2 = boto3.resource('ec2')
    workers = list(ec2.instances.filter(
        Filters=[{'Name': 'tag-value', 'Values': ['ece1779_a2_user']},
                 {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]))
    if num_destroy > len(workers):
        return False
    else:
        random.shuffle(workers)
        for i in range(num_destroy):
            workers[i].terminate()
        return True
