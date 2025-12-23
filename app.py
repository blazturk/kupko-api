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

    # meal_type: case-insensitive match (use ilike)
    meal_type = args.get('meal_type')
    if meal_type:
        filters.append(Meal.meal_type.ilike(meal_type))

    # price: convert to float safely
    price = args.get('price')
    if price:
        try:
            price_val = float(price)
            filters.append(Meal.price <= price_val)
        except ValueError:
            # ignore invalid price or optionally raise a 400
            pass

    # prep_time: convert to int safely (or float if that's your schema)
    prep_time = args.get('prep_time')
    if prep_time:
        try:
            prep_val = int(prep_time)
            filters.append(Meal.prep_time == prep_val)
        except ValueError:
            pass

    # allergies: exclude any meal that contains ANY of the forbidden allergens.
    # Use coalesce to make NULL become '' so concat/like doesn't become NULL.
    allergies_param = args.get('allergies')
    if allergies_param:
        # Parse and normalize
        allergies = [a.strip().lower() for a in allergies_param.split(',') if a.strip()]
        if allergies:
            allergy_filters = []
            # Build: lower(concat(',', coalesce(allergies,''), ',')) LIKE '%,allergy,%'
            allergies_field = func.lower(func.concat(',', func.coalesce(Meal.allergies, ''), ','))
            for allergy in allergies:
                pattern = f'%,{allergy},%'
                allergy_filters.append(allergies_field.like(pattern))

            # Exclude meals where ANY allergy matches: i.e. NOT (any LIKE)
            # But keep meals that have no allergy info (NULL/empty) as allowed.
            filters.append(
                or_(
                    Meal.allergies.is_(None),
                    Meal.allergies == '',
                    not_(or_(*allergy_filters))
                )
            )
        else:
            # allergies param provided but ended up empty after parsing; ignore
            pass

    return filters


@app.route('/random_menu/<n>/<times_of_day_list>/<time>/<allergies>/<max_price>/<meal_type>', methods=['GET'])
def get_random_menu(n, times_of_day_list, time, allergies, max_price, meal_type):
    # Parse allergies from the route parameter
    allergy_list = [a.strip().lower() for a in allergies.split(',') if a.strip()]

    # Build filters once from the request arguments
    filters = build_filters_from_args(request.args)

    menu = []
    for day_index in range(int(n)):
        daily_meals = []
        times_of_day = times_of_day_list.split(',')

        for tod in times_of_day:
            # Start with the base query
            query = Meal.query.filter(
                *filters,
                Meal.time_of_day == tod,
                Meal.prep_time == time,
                Meal.price <= max_price,
                Meal.meal_type == meal_type
            )

            # Exclude meals that contain any of the specified allergens
            # Assuming Meal.allergens is a comma-separated string like "dairy,nuts,gluten"
            if allergy_list:
                # Create a filter for each allergen
                for allergen in allergy_list:
                    # This excludes meals where the allergen appears in the comma-separated list
                    # The ilike with wildcards ensures we match the allergen anywhere in the list
                    query = query.filter(
                        ~Meal.allergies.ilike(f'%{allergen}%')
                    )

            # Get random meal that doesn't contain any allergens
            meal = query.order_by(func.random()).first()

            if meal:
                daily_meals.append(meal)

        menu.append({
            "day": day_index + 1,
            "menu": meals_schema.dump(daily_meals)
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

