from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database_setup import Base, Category, Item
from flask import session as login_session


app = Flask(__name__)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
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
    # return "This page will show all my categories"
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




if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
