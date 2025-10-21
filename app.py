import secrets

import os

from datetime import date
from flask import (
    flash,
    Flask,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from functools import wraps

from macro_mojo.utils import (
    error_for_date_format,
    error_for_nutrition_entry,
    error_for_meal_len,
    error_for_targets,
    get_todays_date,
    is_date_in_url_valid,
    is_nutrition_id_valid,
)

from macro_mojo.ai_agent import get_ai_response, get_ai_welcome_message

# from werkzeug.exceptions import NotFound
from macro_mojo.db_persistence import DatabasePersistence

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


def user_logged_in():
    return "username" in session


def check_login(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not user_logged_in():
            flash("You must be logged in to complete the action.")
            return redirect(url_for("dispay_login_page", next=request.url))

        return func(*args, **kwargs)

    return decorated_function


def _paginate(data, page_str):
    if page_str is None:
        page_str = "1"

    try:
        page = int(page_str)
    except ValueError:
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
    dsn = app.config.get("DATABASE_URL") or os.environ.get("DATABASE_URL")
    g.storage = DatabasePersistence(dsn=dsn)


@app.route("/favicon.ico/")
def favicon():
    return make_response("", 204)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login/")
def dispay_login_page():
    return render_template("login.html")


@app.route("/login/", methods=["POST"])
def process_login():
    username = request.form["username"]
    password = request.form["pwd"]
    next_url = request.form["next"]

    if g.storage.find_login(username, password):
        session["username"] = username
        session.permanent = True
        flash("Log in successful!")
        if next_url:
            return redirect(next_url)
        return redirect(url_for("user_overview", username=username))
    else:
        flash("Invalid credentials. Try again!")
        return render_template("login.html"), 422


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/<username>/")
@check_login
def user_overview(username):
    user_targets = g.storage.get_user_targets(username)
    user_nutrition = g.storage.get_user_all_nutrition(username)
    today = date.today()

    # Pagination
    page_str = request.args.get("page")
    pagination_params = _paginate(user_nutrition, page_str)
    if not pagination_params:
        return render_template("bad_url.html", username=username)

    page, start, end, total_pages = pagination_params
    user_nutrition_on_page = user_nutrition[start:end]
    return render_template(
        "dashboard.html",
        username=username,
        user_targets=user_targets,
        user_nutrition_on_page=user_nutrition_on_page,
        total_pages=total_pages,
        page=page,
        date=today,
    )


@app.route("/<username>/<date>")
@check_login
def day_view(username, date):
    if not is_date_in_url_valid(date):
        return render_template("bad_url.html", username=username)

    daily_total = g.storage.daily_total_nutrition(username, date)
    nutrition_left = g.storage.get_nutrition_left(username, date)
    daily_nutrition = g.storage.get_daily_nutrition(username, date)
    if not daily_nutrition:
        return render_template("empty_day.html", date=date, username=username)

    page_str = request.args.get("page")
    pagination_params = _paginate(daily_nutrition, page_str)
    if not pagination_params:
        return render_template("bad_url.html", username=username)

    page, start, end, total_pages = pagination_params
    daily_nutrition_entries_on_page = daily_nutrition[start:end]
    return render_template(
        "day_view.html",
        username=username,
        daily_nutrition_entries_on_page=daily_nutrition_entries_on_page,
        total_pages=total_pages,
        page=page,
        date=date,
        daily_total=daily_total,
        nutrition_left=nutrition_left,
    )


@app.route("/<username>/<date>/add_new")
@check_login
def new_nutrition_entry(username, date):
    if not is_date_in_url_valid(date):
        return render_template("bad_url.html", username=username)
    return render_template(
        "add_nutrition_entry.html",
        username=username,
        date=date,
        input_nutrition={},
        today=get_todays_date(),
    )


@app.route("/<username>/<date>/add_new", methods=["POST"])
@check_login
def add_nutrition_entry(username, date):
    if not is_date_in_url_valid(date):
        return render_template("bad_url.html", username=username)
    # Extract entered data
    entry_date = request.form["entry_date"]
    calories = request.form["calories"]
    protein = request.form["protein"]
    fat = request.form["fat"]
    carbs = request.form["carbs"]
    meal = request.form["meal"]

    # Validate inputs, display errors and re-display template with input values
    errors = []
    error_date = error_for_date_format(entry_date)
    if error_date:
        errors.append(error_date)
    error_nutrition = error_for_nutrition_entry(calories, protein, fat, carbs)
    if error_nutrition:
        errors.append(error_nutrition)
    error_meal = error_for_meal_len(meal)
    if error_meal:
        errors.append(error_meal)

    if errors:
        for error in errors:
            flash(error)
        input_nutrition = {
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
            "meal": meal,
        }
        return render_template(
            "add_nutrition_entry.html",
            username=username,
            date=entry_date,
            input_nutrition=input_nutrition,
        )

    # Execute queries to add data
    g.storage.add_nutrition_entry(
        entry_date, username, calories, protein, fat, carbs, meal
    )
    flash("New data entry added!")
    return redirect(url_for("day_view", username=username, date=entry_date))


@app.route("/<username>/targets")
@check_login
def display_targets(username):
    user_targets = g.storage.get_user_targets(username)
    return render_template(
        "targets.html", username=username, user_targets=user_targets
    )


@app.route("/<username>/targets/edit")
@check_login
def edit_targets(username):
    user_targets = g.storage.get_user_targets(username)
    return render_template(
        "edit_targets.html", username=username, user_targets=user_targets
    )


@app.route("/<username>/targets/edit", methods=["POST"])
@check_login
def update_targets(username):
    # Extract new target values from HTTP request
    new_calorie_target = request.form["calories"]
    new_protein_target = request.form["protein"]
    new_fat_target = request.form["fat"]
    new_carb_target = request.form["carbs"]

    # Validate inputs, display errors and re-display template with input values
    error = error_for_targets(
        new_calorie_target, new_protein_target, new_fat_target, new_carb_target
    )
    if error:
        flash(error)
        input_user_targets = {
            "calorie_target": new_calorie_target,
            "protein_target": new_protein_target,
            "fat_target": new_fat_target,
            "carb_target": new_carb_target,
        }
        return render_template(
            "edit_targets.html",
            username=username,
            user_targets=input_user_targets,
        )
    # Execute SQL queries to update the targets
    g.storage.update_user_targets(
        username,
        new_calorie_target,
        new_protein_target,
        new_fat_target,
        new_carb_target,
    )

    flash("Targets were updated!")
    return redirect(url_for("display_targets", username=username))


@app.route("/<username>/<date>/<int:nutrition_entry_id>/edit")
@check_login
def edit_entry(username, date, nutrition_entry_id):
    # Validate date part of URL
    if not is_date_in_url_valid(date):
        return render_template("bad_url.html", username=username)

    # Validate nutrition id part of URL
    available_nutrition_ids = g.storage.get_all_nutrition_entries_ids(username)
    if not is_nutrition_id_valid(nutrition_entry_id, available_nutrition_ids):
        return render_template("bad_url.html", username=username)

    # Get nutrition data to diplay in `edit_entry` view
    nutrition_data = g.storage.find_nutrition_entry_by_id(nutrition_entry_id)
    return render_template(
        "edit_entry.html",
        username=username,
        date=date,
        nutrition_data=nutrition_data,
        nutrition_entry_id=nutrition_entry_id,
    )


@app.route(
    "/<username>/<date>/<int:nutrition_entry_id>/edit", methods=["POST"]
)
@check_login
def update_entry(username, date, nutrition_entry_id):
    # Validate date part of URL
    if not is_date_in_url_valid(date):
        return render_template("bad_url.html", username=username)

    # Validate nutrition id part of URL
    available_nutrition_ids = g.storage.get_all_nutrition_entries_ids(username)
    if not is_nutrition_id_valid(nutrition_entry_id, available_nutrition_ids):
        return render_template("bad_url.html", username=username)

    # Extract new values from HTTP request
    calories = request.form["calories"]
    protein = request.form["protein"]
    fat = request.form["fat"]
    carbs = request.form["carbs"]
    meal = request.form["meal"]

    # Validate data. If input not valid, display error and re-display input
    # values
    errors = []
    error_nutrition = error_for_nutrition_entry(calories, protein, fat, carbs)
    if error_nutrition:
        errors.append(error_nutrition)
    error_meal = error_for_meal_len(meal)
    if error_meal:
        errors.append(error_meal)
    if errors:
        for error in errors:
            flash(error)
        input_nutrition = {
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
            "meal": meal,
        }
        return render_template(
            "edit_entry.html",
            username=username,
            date=date,
            nutrition_entry_id=nutrition_entry_id,
            nutrition_data=input_nutrition,
        )

    g.storage.update_nutrition_entry(
        nutrition_entry_id, calories, protein, fat, carbs, meal
    )
    flash("The entry was updated!")
    return redirect(url_for("day_view", username=username, date=date))


@app.route(
    "/<username>/<date>/<int:nutrition_entry_id>/delete", methods=["POST"]
)
@check_login
def delete_entry(username, date, nutrition_entry_id):
    # Validate date part of URL
    if not is_date_in_url_valid(date):
        return render_template("bad_url.html", username=username)

    # Validate nutrition id part of URL
    available_nutrition_ids = g.storage.get_all_nutrition_entries_ids(username)
    if not is_nutrition_id_valid(nutrition_entry_id, available_nutrition_ids):
        return render_template("bad_url.html", username=username)

    g.storage.delete_nutrition_entry(nutrition_entry_id)
    flash("The entry was deleted!")
    return redirect(url_for("day_view", username=username, date=date))


@app.route("/<username>/ai_assistant")
@check_login
def chat_with_ai_assistant(username):
    if "history" not in session or not session["history"]:
        welcome_message = get_ai_welcome_message()
        session["history"] = []
        session["history"].append(
            {"sender": "ai_agent", "text": welcome_message}
        )
    return render_template(
        "ai_help.html", history=session["history"], username=username
    )


@app.route("/<username>/ai_assistant", methods=["POST"])
@check_login
def get_response_from_ai_assistant(username):
    user_message = request.form["message"]
    session["history"].append({"sender": username, "text": user_message})
    ai_message = get_ai_response(user_input=user_message)
    # ai_message_dict = get_ai_response(user_message, session['history'])
    # ai_message = f"{ai_message_dict}"
    # ai_message = f"""
    #              Based on information you provided, suggested targets are:\
    #              - Calories: {ai_message_dict['calories']}
    #              - Protein: {ai_message_dict['protein']} g
    #              - Fat: {ai_message_dict['fat']} g
    #              - Carbohydrates: {ai_message_dict['carbs']} g

    #              Explanation:
    #              {ai_message_dict['explanation']}
    # """
    session["history"].append({"sender": "ai_agent", "text": ai_message})

    session.modified = True
    return redirect(url_for("chat_with_ai_assistant", username=username))


@app.route("/<username>/ai_assistant/clear_history", methods=["POST"])
@check_login
def clear_chat_history(username):
    session["history"].clear()
    return redirect(url_for("chat_with_ai_assistant", username=username))


if __name__ == "__main__":
    if os.environ.get("FLASK_ENV") == "production":
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)
