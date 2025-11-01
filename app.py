from flask import Flask, request, jsonify
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

from marshmallow_sqlalchemy import SQLAlchemySchema

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Database

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

#Meal Class/Model
class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    meal_type = db.Column(db.String(100), nullable=False)

def __init__(self, name, price, meal_type):
    self.name = name
    self.price = price
    self.meal_type = meal_type

# Product Schema
class MealSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Meal
        load_instance = True

#Init schema
meal_schema = MealSchema()
meals_schema = MealSchema(many=True)

#Create meal
@app.route('/meal', methods=['POST'])
def create_meal():
    name = request.json['name']
    price = request.json['price']
    meal_type = request.json['meal_type']

    new_meal = Meal(name=name, price=price, meal_type=meal_type)
    db.session.add(new_meal)
    db.session.commit()
    return meal_schema.jsonify(new_meal)

#Get all meals
@app.route('/meal', methods=['GET'])
def get_meals():
    all_meals = Meal.query.all()
    result = meals_schema.dump(all_meals)
    return jsonify(result)

#Get single meal
@app.route('/meal/<id>', methods=['GET'])
def get_meal(id):
    meal = Meal.query.get(id)
    return meal_schema.jsonify(meal)

#Update meal
@app.route('/meal/<id>', methods=['PUT'])
def update_meal(id):
    meal = Meal.query.get(id)
    name = request.json['name']
    price = request.json['price']
    meal_type = request.json['meal_type']

    meal.name = name
    meal.price = price
    meal.meal_type = meal_type
    db.session.commit()
    return meal_schema.jsonify(meal)

#Delete meal
@app.route('/meal/<id>', methods=['DELETE'])
def delete_meal(id):
    meal = Meal.query.get(id)
    db.session.delete(meal)
    db.session.commit()
    return meal_schema.jsonify(meal)

if __name__ == '__main__':
    app.run(debug=True)

