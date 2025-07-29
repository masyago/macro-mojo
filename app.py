import secrets

from datetime import date
from flask import (
    flash,
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from functools import wraps

from calorie_tracker.utils import (
    check_meal_duplicates,
    error_for_nutrition_entry,
    error_for_targets,
    error_for_meal_len,
)


from calorie_tracker.db_persistence import DatabasePersistence

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

def user_logged_in():
    return 'username' in session

def check_login(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not user_logged_in():
            flash('You must be logged in to complete the action.')
            return redirect(url_for('dispay_login_page'))
        
        return func(*args, **kwargs)
        
    return decorated_function

def _paginate(data, page_str):
    if page_str is None:
        page_str = "1"
    
    try:
        page = int(page_str)
    except:
        return False
    
    per_page = 5
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(data) + per_page - 1) // per_page

    if page not in range(1, total_pages + 1):
        return False
    
    return (page, start, end, total_pages)
    

@app.before_request
def load_db():
    g.storage = DatabasePersistence()

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login")
def dispay_login_page():
    return render_template('login.html')

@app.route("/login", methods=["POST"])
def process_login():
    username = request.form["username"]
    password = request.form["pwd"]

    if g.storage.find_login(username, password):
        session['username'] = username
        session.permanent = True
        flash("Log in successful!")
        return redirect(url_for('user_overview', username=username))
    else:
        flash('Invalid credentials. Try again!')
        return render_template('login.html'), 422

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route("/<username>")
@check_login
def user_overview(username):
    user_targets = g.storage.get_user_targets(username)
    user_nutrition = g.storage.get_user_all_nutrition(username)
    today = date.today()
    
    # Pagination
    page_str = request.args.get('page')
    pagination_params = _paginate(user_nutrition, page_str)
    # return f"{pagination_params}"
    # return f"{_paginate(user_nutrition, page_str)}"
    if not pagination_params:
        return "The page does not exist."
    
    page, start, end, total_pages = pagination_params
    # return f"{page}, {start}, {end}, {total_pages}"
    
    user_nutrition_on_page = user_nutrition[start:end]
    # return f"{user_nutrition_on_page}"

    return render_template('dashboard.html', username=username, 
                           user_targets=user_targets, user_nutrition_on_page=user_nutrition_on_page,
                           total_pages=total_pages, page=page, date=today)
                           
@app.route("/<username>/<date>")
@check_login
def day_view(username, date):
    daily_total = g.storage.daily_total_nutrition(username, date)
    nutrition_left = g.storage.get_nutrition_left(username, date)
    daily_nutrition = g.storage.get_daily_nutrition(username, date)

    page_str = request.args.get('page')
    pagination_params = _paginate(daily_nutrition, page_str)
    if not pagination_params:
        return "The page does not exist."
    
    page, start, end, total_pages = pagination_params

    daily_nutrition_entries_on_page = daily_nutrition[start:end]

    return render_template('day_view.html', username=username, daily_nutrition_entries_on_page=daily_nutrition_entries_on_page,
                           total_pages=total_pages, page=page, date=date, daily_total=daily_total, nutrition_left=nutrition_left)

@app.route("/<username>/<date>/add_new") 
@check_login
def new_nutrition_entry(username, date):
    user_meals = g.storage.get_user_meals(username)
    return render_template('add_nutrition_entry.html', username=username, date=date, user_meals=user_meals, input_nutrition={})

@app.route("/<username>/<date>/add_new", methods=["POST"])
@check_login
def add_nutrition_entry(username, date):
    # Extract entered data
    calories = request.form["calories"]
    protein = request.form["protein"]
    fat = request.form["fat"]
    carbs = request.form["carbs"]
    meal = request.form["meal"]

    # Validate data. If input not valid, display error and user entries
    error = error_for_nutrition_entry(calories, protein, fat, carbs)
    if error:
        flash(error)
        input_nutrition = {'calories': calories,
                              'protein': protein,
                              'fat': fat,
                              'carbs': carbs,
                              'meal': meal,
                            }
        user_meals = g.storage.get_user_meals(username)
        return render_template('add_nutrition_entry.html', username=username, date=date, input_nutrition=input_nutrition, user_meals=user_meals)

    # Execute queries to add data
    g.storage.add_nutrition_entry(date, username,
                            calories, protein, fat, carbs, meal)
    flash('New data entry added!')
    return redirect(url_for('day_view', username=username, date=date))

@app.route("/<username>/targets")
@check_login
def display_targets(username):
    user_targets = g.storage.get_user_targets(username=username)
    return render_template('targets.html', username=username,
                           user_targets=user_targets)

@app.route("/<username>/targets/edit")
@check_login
def edit_targets(username):
    user_targets = g.storage.get_user_targets(username=username)
    return render_template('edit_targets.html', username=username, user_targets=user_targets)

@app.route("/<username>/targets/edit", methods=["POST"])
@check_login
def update_targets(username):
    # Extract new target values from HTTP request
    new_calorie_target = request.form["calories"]
    new_protein_target = request.form["protein"]
    new_fat_target = request.form["fat"]
    new_carb_target = request.form["carbs"]

    error = error_for_targets(new_calorie_target, new_protein_target,
                      new_fat_target, new_carb_target)
    if error:
        flash(error)
        input_user_targets = {'calorie_target' : new_calorie_target,
                              'protein_target' : new_protein_target, 
                              'fat_target' : new_fat_target,
                               'carb_target' : new_carb_target }
        return render_template('edit_targets.html', username=username, user_targets=input_user_targets)
    # Execute SQL queries to update the targets
    g.storage.update_user_targets(username,
                            new_calorie_target, new_protein_target,
                            new_fat_target, new_carb_target)
    
    flash('Targets were updated!')
    return redirect(url_for('display_targets', username=username))

@app.route("/<username>/<date>/<int:nutrition_entry_id>/edit")
@check_login
def edit_entry(username, date, nutrition_entry_id):
    # Need to pass meal associated with entry to diplay in edit view
    user_meals = g.storage.get_user_meals(username)
    nutrition_data = g.storage.find_nutrition_entry_by_id(username, nutrition_entry_id)

    return render_template('edit_entry.html', username=username, date=date,
                           nutrition_data=nutrition_data,
                           nutrition_entry_id=nutrition_entry_id, user_meals=user_meals)

@app.route("/<username>/<date>/<int:nutrition_entry_id>/edit", methods=["POST"])
@check_login
def update_entry(username, date, nutrition_entry_id):
    calories = request.form["calories"]
    protein = request.form["protein"]
    fat = request.form["fat"]
    carbs = request.form["carbs"]
    meal = request.form["meal"]

    # Validate data. If input not valid, display error and user entries
    error = error_for_nutrition_entry(calories, protein, fat, carbs)
    if error:
        flash(error)
        input_nutrition = {'calories': calories,
                              'protein': protein,
                              'fat': fat,
                              'carbs': carbs,
                              'meal': meal,
                            }
        user_meals = g.storage.get_user_meals(username)
        return render_template('edit_entry.html', username=username, date=date, nutrition_entry_id=nutrition_entry_id, nutrition_data=input_nutrition, user_meals=user_meals)

    g.storage.update_nutrition_entry(nutrition_entry_id, calories,
                                     protein, fat, carbs, meal)
    flash('The entry was updated!')
    return redirect(url_for('day_view', username=username, date=date))

@app.route("/<username>/<date>/<int:nutrition_entry_id>/delete", methods=["POST"])
@check_login
def delete_entry(username, date, nutrition_entry_id):
    g.storage.delete_nutrition_entry(nutrition_entry_id)
    flash('The entry was deleted!')
    return redirect(url_for('day_view', username=username, date=date))

@app.route("/<username>/meals")
@check_login
def display_meals(username):
    user_meals = g.storage.get_user_meals(username=username)
    page_str = request.args.get('page')
    pagination_params = _paginate(user_meals, page_str)

    if not pagination_params:
        return "The page does not exist."
    
    page, start, end, total_pages = pagination_params

    user_meals_on_page = user_meals[start:end]
    return render_template('meals.html', username=username,
                           total_pages=total_pages, page=page,
                           user_meals_on_page=user_meals_on_page)

@app.route("/<username>/<int:meal_id>/edit")
@check_login
def edit_meal(username, meal_id):
    meal_data = g.storage.get_meal_data_by_id(meal_id)
    return render_template('edit_meal.html', username=username, meal_data=meal_data)

@app.route("/<username>/<int:meal_id>/edit", methods=["POST"])
@check_login
def update_meal(username, meal_id):
    new_meal = request.form["meal"].strip()
    # Validate data. If input not valid, display error and user entries
    error_len = error_for_meal_len(new_meal)
    if error_len:
        flash(error_len)
        temp_meal_data = {'name': new_meal,
                          'id': meal_id}
        return render_template('edit_meal.html', username=username, meal_data=temp_meal_data)
    
    existing_meals = []
    for item in g.storage.get_all_meal_names_except_current(username, meal_id):
        existing_meals.append(item['name'])

    error_duplicate = check_meal_duplicates(new_meal, existing_meals)
    if error_duplicate:
        flash(error_duplicate)
        temp_meal_data = {'name': new_meal,
                          'id': meal_id}
        return render_template('edit_meal.html', username=username, meal_data=temp_meal_data)
    
    g.storage.update_meal(username, meal_id, new_meal)
    flash('The meal was updated!')
    return redirect(url_for('display_meals', username=username))

@app.route("/<username>/<int:meal_id>/delete", methods=["POST"])
@check_login
def delete_meal(username, meal_id):
    g.storage.delete_meal(meal_id)
    flash('The meal was deleted!')
    return redirect(url_for('display_meals', username=username))

@app.route("/<username>/new_meal") 
@check_login
def new_meal(username):
    return render_template('new_meal.html', username=username)

@app.route("/<username>/new_meal", methods=["POST"])
@check_login
def add_new_meal(username):
    # Extract entered data
    new_meal = request.form["meal"].strip()

    error_len = error_for_meal_len(new_meal)
    if error_len:
        flash(error_len)
        temp_meal_name = new_meal
        return render_template('new_meal.html', username=username, temp_meal_name=temp_meal_name)
    
    existing_meals = []
    for item in g.storage.get_all_meal_names(username):
        existing_meals.append(item['name'])

    error_duplicate = check_meal_duplicates(new_meal, existing_meals)
    if error_duplicate:
        flash(error_duplicate)
        temp_meal_name = new_meal
        return render_template('new_meal.html', username=username, temp_meal_name=temp_meal_name)

    g.storage.add_meal(username, new_meal)
    user_meals = g.storage.get_user_meals(username=username)
    page_str = request.args.get('page')
    pagination_params = _paginate(user_meals, page_str)
    if not pagination_params:
        return "The page does not exist."
    
    page, start, end, total_pages = pagination_params
    user_meals_on_page = user_meals[start:end]
    flash('New meal option was added!')
    return render_template('meals.html', username=username, total_pages=total_pages, page=page,
                           user_meals=user_meals, user_meals_on_page=user_meals_on_page)

if __name__ == "__main__":
    app.run(debug=True, port=5003)


