from flask import render_template, request, session, url_for, redirect, g, jsonify
from app import webapp
from app.config import db_config
from datetime import timedelta
import mysql.connector
import hashlib, random


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


@webapp.route('/login',methods=['GET'])
#display login page
def login():
    uname = None
    error = None

    if 'username' in session:
        uname = session['username']

    if 'error' in session:
        error = session['error']
        session.pop('error')

    return render_template("user/login.html", error=error, username=uname)


@webapp.route('/login_submit', methods=['POST'])
# handle login info from login form
def login_submit():

    uname = request.form.get('username', "")
    password = request.form.get('password', "")

    if uname == "" or password == "":
        error = "Error: All fields are required!"
        return render_template("user/login.html",title="Main Page",error=error,username=uname,)

    # validate user from database
    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT * FROM user WHERE username = %s"
    cursor.execute(query,(uname,))

    row = cursor.fetchone()
    if row == None:
        return render_template("user/login.html",title="Main Page",error="User not existed!")

    user_id = row[0]
    username = row[1]
    hash = row[2]
    salt = row[3]

    salted_password = "{}{}".format(salt, password)
    m = hashlib.md5()
    m.update(salted_password.encode('utf-8'))
    new_hash = m.digest()

    if new_hash == hash:
        session['authenticated'] = True
        session.permanent = True
        session['username'] = username
        session['user_id'] = user_id
        if 'error' in session:
            session.pop('error')
        return redirect(url_for('thumbnails',id=user_id))

    session['error'] = "Error! Incorrect username or password!"
    return render_template("user/login.html",title="Main Page",error="Error! Incorrect username or password!")


@webapp.route('/new_user', methods=['GET','POST'])
# request new user form
def new_user():
    uname = None
    error = None

    if 'username' in session:
        uname = session['username']

    if 'error' in session:
        error = session['error']
        session.pop('error')

    return render_template("user/new.html", error=error, username=uname)




@webapp.route('/new_user_submit', methods=['POST'])
#handle new user form, create new user
def new_user_submit():

    username = request.form.get('username', "")
    password = request.form.get('password', "")
    confirm_pw = request.form.get('confirm', "")

    # validate input and password
    if username == "" or password == "":
        error = "Error: All fields are required!"
        return render_template("user/new.html", title="New User", error=error, username=username )
    if password != confirm_pw:
        error = "Error: Re-entered password unmatched!"
        return render_template("user/new.html", title="New User", error=error, username=username)

    #check if username existed
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT * FROM user WHERE username = %s '''
    cursor.execute(query, (username,))
    row = cursor.fetchone()

    if row != None:
        error = "Error: User ID exsited!"
        return render_template("user/new.html",title="New User", error=error)

    try:
        # save new user with hash and salt password
        cnx = get_db()
        cursor = cnx.cursor()
        query = "INSERT INTO user (username,hash,salt) VALUES (%s,%s,%s)"

        salt = str(random.getrandbits(16))
        salted_password = "{}{}".format(salt,password)
        m = hashlib.md5()
        m.update(salted_password.encode('utf-8'))
        hash = m.digest()

        cursor.execute(query,(username, hash, salt))
        cursor.close()
        cnx.commit()

    except Exception as error:
        cnx.rollback()
        session['error'] = str(error)
        return redirect(url_for('new_user'))

    if 'error' in session:
        session.pop('error')
    return render_template("user/login.html",title="Main Page",username=username)


@webapp.route('/logout', methods=['GET', 'POST'])
# log out from current user
def logout():
    session.clear()
    return redirect(url_for('login'))



@webapp.route("/api/register",methods=['POST'])
# URL endpoints for register API
def api_register():
    username = request.form.get("username")
    password = request.form.get("password")

    # validate input and password
    if username == "" or password == "":
        message = {"status": 400,
                   "message": "Bad Request: invalid username or password"}
        response = jsonify(message)
        response.status_code = 400
        return response

    # check if username existed
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT * FROM user WHERE username = %s '''
    cursor.execute(query, (username,))
    row = cursor.fetchone()

    if row != None:
        message = {"status": 409,
                   "message": "Conflict: username existed"}
        response = jsonify(message)
        response.status_code = 409
        return response

    # save new user
    cnx = get_db()
    cursor = cnx.cursor()
    query = "INSERT INTO user (username,hash,salt) VALUES (%s,%s,%s)"

    salt = str(random.getrandbits(16))
    salted_password = "{}{}".format(salt, password)
    m = hashlib.md5()
    m.update(salted_password.encode('utf-8'))
    hash = m.digest()

    cursor.execute(query, (username, hash, salt))
    cursor.close()
    cnx.commit()

    message = {"status":201,
               "message": "Created",
               "username":username}
    response = jsonify(message)
    response.status_code = 201
    return response
