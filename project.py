from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from database_setup import Base, Category, Item, User
from flask import session as login_session

from apiclient import discovery
import httplib2
from oauth2client import client

import json
from functools import wraps



app = Flask(__name__)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']



def require_login(function):
    @wraps(function)
    def wrapper(*args,**kwargs):
        if 'GoogleUID' not in login_session:
            flash('login required')
            return redirect('/')
        else:
            #check that access token is valid
            access_token = login_session['access_token']
            url = (
            'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
            %access_token)

            h=httplib2.Http()
            result = json.loads(h.request(url, 'GET')[1])
            if result.get('error' is not None):
                flash('Authentication error, please try logging in again.')
                return redirect('/')
            #check if token is valid for this application
            if result['issued_to'] != CLIENT_ID:
                flash('Authentication error, please try logging in again.')
                return redirect('/')

            return function(*args,**kwargs)
    return wrapper

def require_ownership(function):
    @wraps(function)
    def wrapper(**kwargs):
        if 'item_id' in kwargs:
            item_id=kwargs['item_id']
            obj = session.query(Item).filter_by(id=item_id).one()

        elif 'category_id' in kwargs:
            category_id = kwargs['category_id']
            obj = session.query(Category).filter_by(id=category_id).one()

        user = getUserInfo(login_session)

        if user.id == obj.user.id:
            return function(**kwargs)

        else:
            flash('You must own this object to perform this action.')
            return redirect('/')

    return wrapper


def createUser(login_session):
    newUser = User(GoogleUID = login_session['GoogleUID'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(GoogleUID = login_session['GoogleUID']
    ).one()
    return user


def getUserInfo(login_session):
    user = session.query(User).filter_by(GoogleUID = login_session['GoogleUID']
    ).one()
    return user


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # (Receive auth_code by HTTPS POST)
    auth_code=request.data

    # If this request does not have `X-Requested-With` header, this could be a CSRF
    if not request.headers.get('X-Requested-With'):
        abort(403)

    # Set path to the Web application client_secret_*.json file you downloaded from the
    # Google API Console: https://console.developers.google.com/apis/credentials
    CLIENT_SECRET_FILE = 'client_secret.json'

    # Exchange auth code for access token, refresh token, and ID token
    credentials = client.credentials_from_clientsecrets_and_code(
        CLIENT_SECRET_FILE,
        ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
        auth_code)

    # Call Google API
    http_auth = credentials.authorize(httplib2.Http())

    # Get profile info from ID token
    GoogleUID = credentials.id_token['sub']
    login_session['access_token'] = credentials.access_token
    login_session['GoogleUID'] = GoogleUID

    # See if a user exists, if it doesn't make a new one
    try:
        user = getUserInfo(login_session)
    except NoResultFound:
        user = createUser(login_session)


    return user.GoogleUID

@app.route('/gdisconnect', methods=['GET'])
def gdisconnect():
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        login_session.clear()
        return redirect('/')
    else:
        flash('error logging out')
        return redirect('/')

# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
@require_login
def newCategory():
    if request.method == 'POST':
        user = getUserInfo(login_session)
        newCategory = Category(name=request.form['name'],user_id=user.id)
        session.add(newCategory)
        try:
            session.commit()
            return redirect("/")
        except IntegrityError:
            session.rollback();
            return "IntegrityError"
    else:
        categories = session.query(Category).all()
        return render_template("createeditcategory.html",categories=categories)

# Show all categories
@app.route('/')
def showCategories():
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)

#Show a specific category
@app.route('/category/<int:category_id>/')
def showCategory(category_id):
    categories = session.query(Category).all()
    category_to_show = session.query(Category).filter_by(id=category_id).one()
    return render_template("categories.html",categories=categories,category=category_to_show)

#Edit a Category
@app.route(
    '/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@require_login
@require_ownership
def editCategory(category_id):
    category_to_edit = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()
    if request.method == 'POST':
        category_to_edit.name = request.form['name']
        return redirect(url_for('showCategory',category_id=category_to_edit.id))
    else:

        return render_template("createeditcategory.html",categories=categories,category=category_to_edit)

# Delete a Category
@app.route(
    '/category/<int:category_id>/delete/', methods=['GET'])
@require_login
@require_ownership
def deleteCategory(category_id):
    categories = session.query(Category).all()
    category_to_delete = session.query(Category).filter_by(id=category_id).one()
    session.delete(category_to_delete)
    session.commit()
    return redirect(url_for('showCategories',categories=categories))


# Create new item
@app.route(
    '/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
@require_login
def newItem(category_id):
    categories = session.query(Category).all()
    if request.method == 'POST':
        user = getUserInfo(login_session)
        newItem = Item(name=request.form['name'],
            description=request.form['description'],
            category_id=category_id,user_id=user.id)
        session.add(newItem)
        try:
            session.commit()
            return redirect(url_for('showCategory',category_id=category_id))
        except IntegrityError:
            session.rollback();
            return "IntegrityError"
    else:
        return render_template("createedititem.html",categories=categories)

# Edit an Item
@app.route(
    '/category/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
@require_login
@require_ownership
def editItem(category_id,item_id):
    item_to_edit = session.query(Item).filter_by(id=item_id).one()

    if request.method == 'POST':
        item_to_edit.name = request.form['name']
        item_to_edit.description = request.form['description']
        return redirect(url_for('showCategory',category_id=category_id))
    else:
        categories = session.query(Category).all()
        return render_template("createedititem.html",categories=categories,item=item_to_edit)

# Delete an Item
@app.route(
    '/category/<int:category_id>/<int:item_id>/delete/',
    methods=['GET', 'POST'])
@require_login
@require_ownership
def deleteItem(category_id,item_id):
    item_to_edit = session.query(Item).filter_by(id=item_id).one()
    session.delete(item_to_edit)
    session.commit()
    categories = session.query(Category).all()
    return redirect(url_for('showCategory',category_id=category_id))



if __name__ == '__main__':
    app.secret_key = 'Random_Secret_String'
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
