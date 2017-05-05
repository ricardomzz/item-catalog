import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    GoogleUID = Column(String(250), nullable=False, unique=True)

class Category(Base):
    __tablename__ = 'Category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship(User,backref=backref('categories'))


    @property
    def serialize(self):
        """Return object data in serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'user': self.user.GoogleUID,
            'user_id': self.user_id,
            'items': [i.serialize for i in self.items]
        }


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('Category.id'))
    category = relationship(Category,backref=backref('items',cascade='delete'))
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship(User,backref=backref('items'))

    @property
    def serialize(self):
        """Return object data in serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'category': self.category.name,
            'category_id': self.category_id,
            'user': self.user.GoogleUID,
            'user_id': self.user_id
        }


engine = create_engine('sqlite:////var/www/html/item-catalog/itemcatalog.db?check_same_thread=False')


Base.metadata.create_all(engine)
