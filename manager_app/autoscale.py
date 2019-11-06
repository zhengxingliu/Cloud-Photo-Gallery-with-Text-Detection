from flask import render_template, redirect, url_for, request, flash, g
from manager_app import manager,config
from manager_app.config import db_config, s3_config

import boto3,random, mysql.connector, statistics, math
from datetime import datetime, timedelta
from operator import itemgetter
from manager_app.ec2 import get_cpu_status


autoscale_config = {"grow_thres": 70, 'shrink_thres': 30, "expand_ratio": 2, "shrink_ratio": 2}

def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

@manager.teardown_appcontext
# this will execute every time when the context is closed
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@manager.route('/config',methods=['GET','POST'])
# view and update current autoscale configuration
def get_config():
    autoscale_config = get_autoscale_config()
    error = None
    return render_template("config.html", title="Autoscale Config", config=autoscale_config, error=error)


def get_autoscale_config():
    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT * FROM autoscale_config WHERE id = 1 "
    cursor.execute(query)
    for key in cursor:
        autoscale_config["grow_thres"] = key[1]
        autoscale_config["shrink_thres"] = key[2]
        autoscale_config["expand_ratio"] = key[3]
        autoscale_config["shrink_ratio"] = key[4]
    return autoscale_config



@manager.route('/update_config',methods=['POST'])
# save new autoscale configuration
def update_config():
    autoscale_config = get_autoscale_config()
    # validate new config values from form
    error = ""
    grow_thres=request.form.get('grow_thres', "")
    if grow_thres != "" :
        if float(grow_thres) > 0 and float(grow_thres) > autoscale_config["shrink_thres"]:
            autoscale_config['grow_thres'] = float(grow_thres)
        else:
            error = "invalid input for grow threshold"

    shrink_thres = request.form.get('shrink_thres', "")
    if shrink_thres != "":
        if float(shrink_thres) > 0 and float(shrink_thres) < autoscale_config["grow_thres"]:
            autoscale_config['shrink_thres'] = float(shrink_thres)
        else:
            error = "invalid input for shrink threshold"

    expand_ratio = request.form.get('expand_ratio', "")
    if expand_ratio != "":
        if float(expand_ratio) > 1:
            autoscale_config['expand_ratio'] = float(expand_ratio)
        else:
            error = "invalid input for expand ratio"

    shrink_ratio = request.form.get('shrink_ratio', "")
    if shrink_ratio != "" :
        if float(shrink_ratio) > 1:
            autoscale_config['shrink_ratio'] = float(shrink_ratio)
        else:
            error = "invalid input for shrink ratio"

    # update config into database
    if error == '':
        cnx = get_db()
        cursor = cnx.cursor()

        query = '''UPDATE autoscale_config
                       SET grow_thres = %s, shrink_thres = %s, expand_ratio = %s, shrink_ratio = %s
                       WHERE id = 1
                   '''
        cursor.execute(query, (
        autoscale_config['grow_thres'], autoscale_config['shrink_thres'], autoscale_config['expand_ratio'],
        autoscale_config['shrink_ratio']))
        cnx.commit()

        return redirect(url_for('get_config'))

    else:
        return render_template("config.html", title="Autoscale Config", config=autoscale_config, error=error)




def get_cpu_average():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(
        Filters=[{'Name': 'tag-value', 'Values': ['ece1779_a2_user']},
                 {'Name': 'instance-state-name', 'Values': ['running']}])


    cpu_list = []
    if len(list(instances)) > 0:
        for instance in instances:
            cpu_status = get_cpu_status(instance.id)
        # read cpu status of each instance for past 2 minutes
        if len(cpu_status) > 0:
            cpu_list.append(cpu_status[-1][1])
        if len(cpu_status) >= 2:
            cpu_list.append(cpu_status[-2][1])
        if len(cpu_list) == 0:
            print('cpu average: no data')
            return 0
        else:
            average = statistics.mean(cpu_list)
            average = round(average, 2)
            print('cpu average utilization is ', average)
            return float(average)
    else:
        return 0
        print('cpu average: no instance')


def autoscale():
    print("autoscale:")
    average = get_cpu_average()
    if average != None:
        print("CPU average: ", average)
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(
            Filters=[{'Name': 'tag-value', 'Values': ['ece1779_a2_user']},
                     {'Name': 'instance-state-name', 'Values': ['running']}])
        size = len(list(instances))

        if size == 0:
            return False

        # expand worker pool when cpu average is higher than expand thres
        elif average > float(autoscale_config["grow_thres"]):
            num = int(size * autoscale_config["expand_ratio"]) - size
            create_instances(num)
            print('average above threshold, creating ' + str(int(size * autoscale_config["expand_ratio"])) + ' workers, ' + str(size+num) + " workers available")
            return True

        # shrink worker pool when cpu average is lower than shrink thres
        elif average < float(autoscale_config["shrink_thres"]):
            num = size - int(size / autoscale_config["shrink_ratio"])
            # at least keep one instance left
            if (size-num) <= 1:
                num = size-1
            destroy_instances(num)
            print('average below threshold, destroying ' + str(int(size * autoscale_config["shrink_ratio"])) + ' workers, '+ str(size-num) + " workers available")
            return True
    return False

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

    # add instance to load balancer
    elb = boto3.client('elb')
    attachinst = elb.register_instances_with_load_balancer(LoadBalancerName='a2loadbalancer',
                                                           Instances=[{'InstanceId': instances[0].id}])


def destroy_instances(num_destroy):
    ec2 = boto3.resource('ec2')
    workers = list(ec2.instances.filter(
        Filters=[{'Name': 'tag-value', 'Values': ['ece1779_a2_user']},
                 {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]))
    if num_destroy > len(workers):
        return False
    else:
        elb = boto3.client('elb')
        random.shuffle(workers)
        for i in range(num_destroy):
            elb.deregister_instances_from_load_balancer(LoadBalancerName='a2loadbalancer',
                                                        Instances=[{'InstanceId': workers[i].id}])
            workers[i].terminate()
        return True



def get_cpu_status(id):

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


    return cpu_stats


