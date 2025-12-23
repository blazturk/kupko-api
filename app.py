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

    # meal_type: case-insensitive match
    meal_type = args.get('meal_type')
    if meal_type:
        filters.append(Meal.meal_type.ilike(meal_type))

    # max_price (not 'price')
    max_price = args.get('max_price')
    if max_price:
        try:
            price_val = float(max_price)
            filters.append(Meal.price <= price_val)
        except ValueError:
            pass

    # prep_time as 'time' parameter
    prep_time = args.get('time')
    if prep_time:
        try:
            prep_val = int(prep_time)
            filters.append(Meal.prep_time <= prep_val)  # Changed to <= (less than or equal)
        except ValueError:
            pass

    # Note: allergies are now handled in the main function, not here
    # Removed the complex allergy logic

    return filters


@app.route('/random_menu', methods=['GET'])
def get_random_menu():
    try:
        n = request.args.get('n', default=7, type=int)
        times_of_day_list = request.args.get('time_of_day', default='breakfast,lunch,dinner', type=str)
        prep_time = request.args.get('time', default=None, type=int)
        allergies = request.args.get('allergies', default=None, type=str)
        max_price = request.args.get('max_price', default=None, type=float)
        meal_type = request.args.get('meal_type', default=None, type=str)

        filters = build_filters_from_args(request.args)
        times_of_day = [tod.strip() for tod in times_of_day_list.split(',') if tod.strip()]

        allergy_list = []
        if allergies and allergies.strip():
            allergy_list = [a.strip().lower() for a in allergies.split(',') if a.strip()]

        # Track used meals PER TIME OF DAY to avoid same meal appearing twice in one day
        # But allow repetition across different days
        menu = []

        for day_index in range(n):
            daily_meals = []
            used_today = set()  # Reset for each day

            for tod in times_of_day:
                query = Meal.query.filter(*filters, Meal.time_of_day == tod)

                # Only exclude meals already used TODAY (not across all days)
                if used_today:
                    query = query.filter(~Meal.id.in_(used_today))

                if allergy_list:
                    for allergen in allergy_list:
                        query = query.filter(
                            or_(
                                Meal.allergies.is_(None),
                                Meal.allergies == '',
                                ~Meal.allergies.ilike(f'%{allergen}%')
                            )
                        )

                meal = query.order_by(func.random()).first()

                if meal:
                    daily_meals.append(meal)
                    used_today.add(meal.id)

            if daily_meals:
                menu.append({
                    "day": day_index + 1,
                    "menu": meals_schema.dump(daily_meals)
                })

        return jsonify(menu)

    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }), 500

@app.route('/')
def index():
    profiles = Meal.query.all()
    return render_template('index.html', profiles=profiles)

@app.route('/add_meal')
def add_data():
    return render_template('add_meal.html')


if __name__ == '__main__':
    app.run(debug=True)

