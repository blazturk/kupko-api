from flask import Flask, request, jsonify, render_template, redirect
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import func, or_, and_, not_
from sqlalchemy.exc import DataError
import os
from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy import text, func

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
    time_of_day = db.Column(db.String(100), nullable=False)
    prep_time = db.Column(db.Integer, nullable=False)
    allergies = db.Column(db.String(255), nullable=False)

def __init__(self, name, price, meal_type, time_of_day, prep_time, allergies):
    self.name = name
    self.price = price
    self.meal_type = meal_type
    self.time_of_day = time_of_day
    self.prep_time = prep_time
    self.allergies = allergies

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
    # Handle both JSON and form submissions safely
    data = request.get_json(silent=True) or request.form

    # Validate keys
    if not all(k in data for k in ('name', 'price', 'meal_type', 'time_of_day', 'prep_time', 'allergies')):
        return jsonify({"error": "Missing required fields"}), 400

    name = data['name']
    price = float(data['price'])
    meal_type = data['meal_type']
    time_of_day = data['time_of_day']
    prep_time = int(data['prep_time'])
    allergies = data['allergies']

    new_meal = Meal(name=name, price=price, meal_type=meal_type, time_of_day=time_of_day, prep_time=prep_time, allergies=allergies)
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
    time_of_day = request.json['time_of_day']
    prep_time = request.json['prep_time']
    allergies = request.json['allergies']

    meal.name = name
    meal.price = price
    meal.meal_type = meal_type
    meal.time_of_day = time_of_day
    meal.prep_time = prep_time
    meal.allergies = allergies
    db.session.commit()
    return meal_schema.jsonify(meal)

#Delete meal
@app.route('/delete/<int:id>')
def erase(id):
    # Deletes the data on the basis of unique id and
    # redirects to home page
    data = Meal.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return redirect('/')


def build_filters_from_args(args):
    filters = []
    # Extract parameters we don't want to process as generic filters
    excluded_params = ['n', 'times_of_day', 'time', 'allergies', 'max_price', 'meal_type']

    for key, value in args.items():
        if key not in excluded_params and value:
            # Add your existing filter logic for other parameters
            # For example:
            if hasattr(Meal, key):
                filters.append(getattr(Meal, key) == value)

    return filters


@app.route('/random_menu', methods=['GET'])
def get_random_menu():
    # Get parameters
    n = request.args.get('n', default=7, type=int)
    time_of_day = request.args.get('time_of_day', default='breakfast,lunch,dinner', type=str)
    prep_time = request.args.get('time', default=None, type=int)  # Changed to int
    allergies = request.args.get('allergies', default='', type=str)
    max_price = request.args.get('max_price', default=None, type=float)
    meal_type = request.args.get('meal_type', default=None, type=str)

    # Parse time_of_day into a list
    time_of_day_list = [tod.strip() for tod in time_of_day.split(',') if tod.strip()]

    # Parse allergies
    allergy_list = []
    if allergies and allergies.strip().lower() not in ['none', 'null', '']:
        allergy_list = [a.strip().lower() for a in allergies.split(',') if a.strip()]

    # Build base filters (excluding the ones we handle separately)
    filters = build_filters_from_args(request.args)

    menu = []
    for day_index in range(n):
        daily_meals = []

        for tod in time_of_day_list:
            # Start with base filters and add time_of_day
            query = Meal.query.filter(*filters, Meal.time_of_day == tod)

            # Apply prep_time filter
            if prep_time is not None:
                query = query.filter(Meal.prep_time <= prep_time)

            # Apply max_price filter
            if max_price is not None:
                query = query.filter(Meal.price <= max_price)

            # Apply meal_type filter
            if meal_type:
                query = query.filter(Meal.meal_type == meal_type)

            # Apply allergy filters
            if allergy_list:
                for allergen in allergy_list:
                    query = query.filter(~Meal.allergies.ilike(f'%{allergen}%'))

            # Get a random meal for this time of day
            meal = query.order_by(func.random()).first()

            if meal:
                daily_meals.append(meal)

        menu.append({
            "day": day_index + 1,
            "meals": meals_schema.dump(daily_meals)
        })

    return jsonify(menu)

@app.route('/')
def index():
    profiles = Meal.query.all()
    return render_template('index.html', profiles=profiles)

@app.route('/add_meal')
def add_data():
    return render_template('add_meal.html')


if __name__ == '__main__':
    app.run(debug=True)

