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





if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
