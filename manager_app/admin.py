from flask import render_template, redirect, url_for, request, flash, g
from manager_app import manager, config
from manager_app.config import db_config, s3_config

import boto3,random, mysql.connector, statistics
from datetime import datetime, timedelta
from operator import itemgetter

from manager_app.ec2 import get_cpu_status
from manager_app.autoscale import get_cpu_average, create_instances, destroy_instances, get_autoscale_config, autoscale


bucket_name = s3_config["bucket"]

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


@manager.route('/', methods=['GET'])
@manager.route('/index', methods=['GET'])
def index():
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    # instances = ec2.instances.all()

    instances = ec2.instances.filter(
        Filters=[{'Name': 'tag-value', 'Values': ['ece1779_a2_user']},
                  {'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    size = len(list(instances))

    cpu_average = get_cpu_average()

    config = get_autoscale_config()

    #autoscale()

    return render_template("index.html", title="EC2 Instances", instances=instances, size=size, cpu_average=cpu_average, config=config)



@manager.route('/view_instance/<id>',methods=['GET'])
# view CPU and request info of selected instance
def view_instance(id):
    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(id)

    cpu_stats = get_cpu_status(instance.id)


    return render_template("view_instance.html", title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats)


@manager.route('/create', methods=['POST'])
def ec2_create():
    create_instances(1)
    flash('New worker created')
    return redirect(url_for('index'))



@manager.route('/destroy', methods=['POST'])
def ec2_destroy():
    if destroy_instances(1):
        flash('Worker destroyed')
        return redirect(url_for('index'))
    else:
        flash ('No worker can be further destroyed')
        return redirect(url_for('index'))


@manager.route('/terminate_all', methods=['POST'])
#terminate all worker instances
def terminate_all():
    ec2 = boto3.resource('ec2')
    workers = list(ec2.instances.filter(
        Filters=[{'Name': 'tag-value', 'Values': ['ece1779_a2_user']}]))
    for instance in workers:
        instance.terminate()
    return redirect(url_for('index'))




@manager.route('/delete_data',methods=['POST'])
# delete all data from database and image files from bucket
def delete_data():
    cnx = get_db()
    cursor = cnx.cursor()

    # delete data from sql database
    query = ''' DELETE FROM transformation'''
    cursor.execute(query)
    query = ''' DELETE FROM photo'''
    cursor.execute(query)
    query = ''' DELETE FROM user'''
    cursor.execute(query)
    cnx.commit()

    # delete images from s3 bucket
    s3 = boto3.resource('s3')
    objects_to_delete = s3.meta.client.list_objects(Bucket=bucket_name)
    delete_keys = {'Objects': []}
    delete_keys['Objects'] = [{'Key': k} for k in [obj['Key'] for obj in objects_to_delete.get('Contents', [])]]
    s3.meta.client.delete_objects(Bucket=bucket_name, Delete=delete_keys)

    return redirect(url_for('index'))



