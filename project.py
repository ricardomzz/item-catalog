from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database_setup import Base, Category, Item
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

def require_login(function):
    @wraps(function)
    def wrapper(*args,**kwargs):
        if 'userid' not in login_session:
            flash('login required')
            return redirect('/')
        else:
            return function(*args,**kwargs)
    return wrapper

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
    #drive_service = discovery.build('drive', 'v3', http=http_auth)
    #appfolder = drive_service.files().get(fileId='appfolder').execute()

    # Get profile info from ID token
    userid = credentials.id_token['sub']
    email = credentials.id_token['email']
    login_session['credentials'] = credentials.to_json()
    login_session['userid'] = userid
    flash('logged in as %s' %login_session['userid'])
    return userid

@app.route('/gdisconnect', methods=['GET'])
def gdisconnect():
    login_session.clear()
    return redirect('/')

# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
@require_login
def newCategory():
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        try:
            session.commit()
            return redirect("/category")
        except IntegrityError:
            session.rollback();
            return "IntegrityError"
    else:
        return render_template("newcategory.html")

# Show all categories
@app.route('/')
@app.route('/category/')
def showCategories():
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)

#Edit a Category
@app.route(
    '/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    category_to_edit = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        category_to_edit.name = request.form['name']
        return redirect(url_for('showCategories'))
    else:
        return render_template("newcategory.html",category=category_to_edit)

# Delete a Category
@app.route(
    '/category/<int:category_id>/delete/', methods=['GET'])
def deleteCategory(category_id):
    category_to_delete = session.query(Category).filter_by(id=category_id).one()
    session.delete(category_to_delete)
    session.commit()
    return redirect(url_for('showCategories'))


# Create new item
@app.route(
    '/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newItem(category_id):
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
        description=request.form['description'],category_id=category_id)
        session.add(newItem)
        try:
            session.commit()
            return redirect("/category")
        except IntegrityError:
            session.rollback();
            return "IntegrityError"
    else:
        return render_template("newitem.html")

# Edit an Item
@app.route(
    '/category/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id,item_id):
    item_to_edit = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        item_to_edit.name = request.form['name']
        item_to_edit.description = request.form['description']
        return redirect(url_for('showCategories'))
    else:
        return render_template("newitem.html",item=item_to_edit)

# Delete an Item
@app.route(
    '/category/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_id,item_id):
    item_to_edit = session.query(Item).filter_by(id=item_id).one()
    session.delete(item_to_edit)
    session.commit()
    return redirect(url_for('showCategories'))



if __name__ == '__main__':
    app.secret_key = 'Random_Secret_String'
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
