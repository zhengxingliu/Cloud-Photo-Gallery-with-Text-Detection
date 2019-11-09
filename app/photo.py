from flask import render_template, request, session, url_for, redirect, g, jsonify
from app import webapp

from app.config import db_config, s3_config
from wand.image import Image

import mysql.connector
import os, hashlib
import boto3

from app.text_detection import text_detection


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
bucket_name = s3_config["bucket"]

# uses amazon RDS mysql database
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


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



@webapp.route('/',methods=['GET'])
# redirect to login, or thumbnail page if already logged in
def main():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    id = session['user_id']
    return redirect(url_for('thumbnails',id=id))


@webapp.route('/<id>/album',methods=['GET',])
# displays thumbnails of all images from current user
def thumbnails(id):
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    cnx = get_db()
    cursor = cnx.cursor()
    # find images from current user
    query = "SELECT p.id, p.user_id, t.filename " \
            "FROM photo p, transformation t " \
            "WHERE p.id = t.photo_id AND t.type_id = 2 AND p.user_id = %s "

    cursor.execute(query, (session['user_id'],))

    # generate urls for images saved in s3, valid for a day
    s3 = boto3.client('s3')
    images = []
    for key in cursor:
        url = s3.generate_presigned_url('get_object',Params={'Bucket': bucket_name,'Key': key[2]},ExpiresIn=86400)
        k = list(key)
        k.append(url)
        images.append(k)

    return render_template("photo/thumbnail.html", image_list=images, id=session['user_id'])


@webapp.route('/<id>/image_upload',methods=['GET'])
# display upload page to upload new image
def image_upload(id):
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    error = None
    if 'error' in session:
        error = session['error']
        session.pop('error')

    return render_template("photo/upload.html", title="Upload Image", error=error,id=session['user_id'])

# check if uploaded file has allowed image extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@webapp.route('/<id>/image_save',methods=['POST'])
# handles photo uploads and text detection
def image_save(id):

    if 'authenticated' not in session:
        return redirect(url_for('image_upload',id=id))

    #check if missing upload file
    if 'file' not in request.files:
        session['error'] = "Missing uploaded file"
        return redirect(url_for('image_upload',id=id))

    new_file = request.files['file']
    if new_file.filename == '':
        session['error'] = 'Missing file name'
        return redirect(url_for('image_upload',id=id))

    # check if file type is not allowed
    if allowed_file(new_file.filename) == False:
        session['error'] = 'File type not supported'
        return redirect(url_for('image_upload',id=id))

    # process file name and type,  add user id prefix before filename
    file_name, file_type = (new_file.filename).rsplit('.',1)
    fname = str(id) + "_" + file_name + "." + file_type


    # check if file existed with duplicated name
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT * FROM transformation WHERE filename = %s'''
    cursor.execute(query, (fname,))
    row = cursor.fetchall()
    if row != []:
        # create new file name with number suffix if file existed
        num = 2
        duplicate = True
        while duplicate == True:
            file_name = file_name.rsplit('__',1)[0] + '__' + str(num)
            fname = str(id) + "_" + file_name + "." + file_type
            query = ''' SELECT * FROM transformation WHERE filename = %s'''
            cursor.execute(query, (fname,))
            num +=1
            if cursor.fetchall() == []:
                duplicate = False

    # save original image at local directory
    fname = str(id) + "_" + file_name + "." + file_type
    ori = os.path.join('app/static/user_images',fname)
    new_file.save(ori)

    # create thumbnail
    img = Image(filename=ori)
    i = img.clone()
    i.resize(80, 100)
    fname_thumbnail = str(id) + "_" + file_name + '_thumbnail.' + file_type
    thumb = os.path.join('app/static/user_images',fname_thumbnail)
    i.save(filename=thumb)

    # create text detection
    fname_textDetection = str(id) + "_" + file_name + '_textDetection.' + file_type
    text = os.path.join('app/static/user_images',fname_textDetection)
    text_detection(ori, text)

    # save to s3 bucket
    s3 = boto3.client('s3')
    with open(ori, "rb") as image1:
        s3.upload_fileobj(image1, bucket_name, fname)
    with open(thumb, "rb") as image2:
        s3.upload_fileobj(image2, bucket_name, fname_thumbnail)
    with open(text, "rb") as image3:
        s3.upload_fileobj(image3, bucket_name, fname_textDetection)

    # remove local files
    os.remove(ori)
    os.remove(thumb)
    os.remove(text)

    # store original photo into database
    query = "INSERT INTO photo (user_id) VALUES (%s)"
    cursor.execute(query, (session['user_id'],))
    query = "SELECT LAST_INSERT_ID()"
    cursor.execute(query)
    row = cursor.fetchone()
    photo_id = row[0]
    query = "INSERT INTO transformation (filename,type_id,photo_id) VALUES (%s,%s,%s)"
    cursor.execute(query, (fname, 1, photo_id))
    # store thumbnail to database
    query = "INSERT INTO transformation (filename,type_id,photo_id) VALUES (%s,%s,%s)"
    cursor.execute(query, (fname_thumbnail, 2, photo_id))
    # store textDetection to database
    query = "INSERT INTO transformation (filename,type_id,photo_id) VALUES (%s,%s,%s)"
    cursor.execute(query, (fname_textDetection, 3, photo_id))

    cursor.close()
    cnx.commit()

    return redirect(url_for('thumbnails',id=id))



@webapp.route('/<id>/image<photo_id>',methods=['GET'])
# display selected image with its original size and text detection
def image_view(id,photo_id):
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    cnx = get_db()
    cursor = cnx.cursor()

    query = "SELECT t.filename FROM transformation t, photo p " \
            "WHERE t.photo_id = p.id AND p.id = %s AND p.user_id = %s AND t.type_id <> 2"
    cursor.execute(query, (photo_id, session['user_id']))


    s3 = boto3.client('s3')
    images = []
    for key in cursor:
        # retrieve image from s3 as url
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key[0]}, ExpiresIn=86400)
        images.append(url)

    return render_template("photo/view.html",image_list=images,id=session['user_id'],photo_id=photo_id)



@webapp.route('/<id>/image<photo_id>/delete',methods=['POST'])
# delete image from local directory and database
def image_delete(id,photo_id):

    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT * FROM transformation t WHERE t.photo_id = %s'''
    cursor.execute(query,(photo_id,))
    row = cursor.fetchall()

    # delete images from s3 bucket
    s3 = boto3.client('s3')
    images = []
    for image in row:
        images.append(image[1])
    objlist = [{'Key': img} for img in images]
    s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objlist})

    # delete image from sql database
    query = ''' DELETE FROM transformation WHERE transformation.photo_id  =%s'''
    cursor.execute(query, (photo_id,))
    query = ''' DELETE FROM photo WHERE photo.id = %s'''
    cursor.execute(query,(photo_id,))
    cnx.commit()

    return redirect(url_for('thumbnails', id=id))


@webapp.route ('/api/upload', methods=['POST'])
# URL endpoints for upload API
def api_upload():

    username = request.form.get("username")
    password = request.form.get("password")

    #validate username and password
    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT * FROM user WHERE username = %s"
    cursor.execute(query, (username,))

    row = cursor.fetchone()
    if row == None:
        message = {"status": 401,
                   "message": "Unauthorized: invalid username or password"}
        response = jsonify(message)
        response.status_code = 401
        return response

    user_id = row[0]
    username = row[1]
    hash = row[2]
    salt = row[3]
    salted_password = "{}{}".format(salt, password)
    m = hashlib.md5()
    m.update(salted_password.encode('utf-8'))
    new_hash = m.digest()
    if new_hash != hash:
        message = {"status": 401,
                   "message": "Unauthorized: invalid username or password"}
        response = jsonify(message)
        response.status_code = 401
        return response

    session['authenticated'] = True
    session['username'] = username
    session['user_id'] = user_id

    # check if uploaded file is valid
    new_file = request.files['file']
    if new_file.filename == '':
        message = {"status": 400,
                   "message": "Bad Request: invalid file"}
        response = jsonify(message)
        response.status_code = 400
        return response

    # upload file
    if allowed_file(new_file.filename) == True :
        try:
            image_save(user_id)

        except:
            message = {"status": 400,
                       "message": "Bad Request: upload failed"}
            response = jsonify(message)
            response.status_code = 400
            return response

    message = {"status": 200,
               "message": "OK"}
    response = jsonify(message)
    response.status_code = 200
    return response


# check if uploaded file has allowed image extensions
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


