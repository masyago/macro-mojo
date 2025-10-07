import unittest
from unittest.mock import patch
from macro_mojo.db_persistence import DatabasePersistence
from contextlib import contextmanager
import bcrypt
import pytest

""" Custom class to simulate `cursor` objects and their behavior """
class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.executed = []
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []

    def execute(self, query, parameters=None):
        self.executed.append((query, parameters))

    def fetchone(self):
        return self.fetchone_result
    
    def fetchall(self):
        return self.fetchall_result
    
    """ Dunder methods for Python context manager protocol"""
    def __enter__(self):
        return self
    
    """ Parameters are: exception type, exception instance, and traceback."""
    def __exit__(self, exc_type, exc, tb):
        pass

""" Custom class to simulate `connection` objects and their behavior """
class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self, cursor_factory=None):
        return self._cursor

"""
Pytest fixture creates a new DatabasePersistence instance for each test. Scoped to functions (default scope)
"""
@pytest.fixture
def dp():
    return DatabasePersistence(dsn="fake_db")

"""
Return a patch.object which is a context manager.
Used to simulate connection to a fake database for tests
"""
def patch_connect(dp, cursor: FakeCursor):
    @contextmanager
    def fake_connect():
        yield FakeConnection(cursor)
    return patch.object(dp, "_database_connect", fake_connect)

"""
Tests for method `find_login`.
1. Correct username and password
2. Incorrect password
3. Username does not exist
"""
def test_find_login_ok(dp):
    # Generate hashed password
    hashed_pwd = bcrypt.hashpw("hungry".encode('utf-8'),
                               bcrypt.gensalt()).decode('utf-8')
    # Instantiate a fake cursor object, pass dict with key-value pair for 
    # hashed password
    cursor = FakeCursor(fetchone_result={"hashed_pwd": hashed_pwd})
    with patch_connect(dp, cursor):
         # Call `find_login` using fake cursor. Returns `True` when username 
         # and password are correct
         login_ok = dp.find_login("cat", "hungry")
    # Check that `find_login` returns `True`
    assert login_ok is True
    # Check that only one SQL was executed
    assert len(cursor.executed) == 1

    # Extract query and parameter from `cursor.executed` and check that they
    # are correct
    query, parameter = cursor.executed[0]
    assert "FROM users" in query
    assert parameter == ("cat",)
    
def test_find_login_wrong_password(dp):
    hashed_pwd = bcrypt.hashpw("hungry".encode('utf-8'),
                               bcrypt.gensalt()).decode('utf-8')
    cursor = FakeCursor(fetchone_result={"hashed_pwd": hashed_pwd})
    with patch_connect(dp, cursor):
        # Call `find_login` using fake cursor. Returns `False` when password
        # is not correct
        login_invalid = dp.find_login("cat", "not_hungry")
    assert login_invalid is False

def test_find_login_wrong_username(dp):
    hashed_pwd = bcrypt.hashpw("hungry".encode('utf-8'),
                               bcrypt.gensalt()).decode('utf-8')
    cursor = FakeCursor(fetchone_result=None)
    with patch_connect(dp, cursor):
        # Call `find_login` using fake cursor. Returns `False` if username 
        # not found
        login_invalid = dp.find_login("snake", "hungry")
    assert login_invalid is False

"""
Tests for method `_find_user_id_by_username`.
1. If user not found, should return `None`
2. If user found, should return corresponding `user_id` value
"""
def test_find_user_id_by_username_not_found(dp):
    cursor = FakeCursor(fetchone_result=None)
    with patch_connect(dp, cursor):
        id_not_found = dp._find_user_id_by_username("dog")
    assert id_not_found is None

def test_find_user_id_by_username_ok(dp):
    cursor = FakeCursor(fetchone_result={"id": 27})
    with patch_connect(dp, cursor):
        id_ok = dp._find_user_id_by_username("hamster")
    assert id_ok == 27

"""
Tests for method `daily_total_nutrition`.
1. Check that the method returns correct `daily_total` when provided username
   and date
2. Returns `None` if rows with the specified date not found
"""
def test_daily_total_nutrition_ok(dp, monkeypatch):
    expected_daily_total = {"calories": 1000, "protein": 34, "fat": 11, 
                            "carbs": 191}
    cursor = FakeCursor(fetchone_result=expected_daily_total)

    # Replace helper method `_find_user_id_by_username` with a spy that takes
    # username as argument and returns `id` value
    captured_username = {}
    def fake_id_lookup(username):
        captured_username['value'] = username
        return 6
    monkeypatch.setattr(dp, "_find_user_id_by_username", fake_id_lookup)

    with patch_connect(dp, cursor):
        test_result = dp.daily_total_nutrition("Mike", "2025-09-14")
    assert test_result == expected_daily_total
    assert captured_username['value'] == "Mike"
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT SUM(calories)" in query
    assert parameters == (6, '2025-09-14')

def test_daily_total_nutrition_no_rows(dp, monkeypatch):
    cursor = FakeCursor(fetchone_result=None)
    monkeypatch.setattr(dp, "_find_user_id_by_username", lambda username: 5)

    with patch_connect(dp, cursor):
        test_result = dp.daily_total_nutrition("Mike", "2025-03-14")
    assert test_result is None
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT SUM(calories)" in query
    assert parameters == (5, '2025-03-14')

"""
Tests for method `get_nutrition_left.
1. Check that the method returns correct `nutrition_left` when provided username
   and date
2. Returns `None` if rows with the specified date not found
"""
def test_get_nutrition_left_ok(dp, monkeypatch):
    expected_nutrition_left = {"Calories left": 500, 
                               "Protein left": 30, 
                               "Fat left": 11, 
                               "Carbs left": 10}
    cursor = FakeCursor(fetchone_result=expected_nutrition_left)

    captured_username = {}
    def fake_id_lookup(username):
        captured_username['value'] = username
        return 6
    monkeypatch.setattr(dp, "_find_user_id_by_username", fake_id_lookup)

    with patch_connect(dp, cursor):
        test_result = dp.get_nutrition_left("Mike", "2025-09-14")

    assert test_result == expected_nutrition_left
    assert captured_username['value'] == "Mike"
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT (calorie_target - SUM(calories))" in query
    assert "LEFT OUTER JOIN targets ON target_id" in query
    assert "LEFT OUTER JOIN nutrition ON nutrition" in query
    assert parameters == (6, '2025-09-14')

def test_get_nutrition_left_no_rows(dp, monkeypatch):
    cursor = FakeCursor(fetchone_result=None)
    monkeypatch.setattr(dp, "_find_user_id_by_username", lambda username: 6)

    with patch_connect(dp, cursor):
        test_result = dp.get_nutrition_left("Mike", "2025-03-14")
    assert test_result is None
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT (calorie_target - SUM(calories))" in query
    assert parameters == (6, '2025-03-14')

"""
Tests for method `get_daily_nutrition`. 2 scenarios: with result row and when
result row is None
Note: Switched to pytest parametrization to avoid code duplicates.
"""
@pytest.mark.parametrize("username, date, user_id, fetchall_rows, expected",
            [
                ("Mike", "2025-09-14", 6,
                [
                    {
                        "nutrition_entry_id": 42,
                        "Added at": "10:01 AM",
                        "Calories": 50,
                        "Protein": 1,
                        "Fat": 1,
                        "Carbohydrates": 12,
                        "Meals or snacks": "apple",
                    },
                    {
                        "nutrition_entry_id": 43,
                        "Added at": "10:03 AM",
                        "Calories": 450,
                        "Protein": 30,
                        "Fat": 10,
                        "Carbohydrates": 60,
                        "Meals or snacks": "smoothie",
                        }
                ],
                [
                    {
                        "nutrition_entry_id": 42,
                        "Added at": "10:01 AM",
                        "Calories": 50,
                        "Protein": 1,
                        "Fat": 1,
                        "Carbohydrates": 12,
                        "Meals or snacks": "apple",
                    },
                    {
                        "nutrition_entry_id": 43,
                        "Added at": "10:03 AM",
                        "Calories": 450,
                        "Protein": 30,
                        "Fat": 10,
                        "Carbohydrates": 60,
                        "Meals or snacks": "smoothie",
                    }
                ]
                ),
                ("Mike", "2025-09-14", 6,
                 [],
                 []
                 )
                 ],
                 ids = ["daily_nutrition_with_rows", "daily_nutrition_no_rows"])

def test_get_daily_nutrition_param(
    dp, monkeypatch, username, date, user_id, fetchall_rows, expected
):
    cursor = FakeCursor(fetchall_result=fetchall_rows)
    monkeypatch.setattr(dp, "_find_user_id_by_username", lambda u: user_id)

    with patch_connect(dp, cursor):
        result = dp.get_daily_nutrition(username, date)

    assert result == expected
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "FROM nutrition" in query
    assert parameters == (user_id, date)

def get_daily_nutrition(self, username, date):
    user_id = self._find_user_id_by_username(username)
    # Get all nutrition data, including meals, for specific date
    query = """
            SELECT nutrition.id AS "nutrition_entry_id",
                    TO_CHAR(entered_at, 'HH:MI AM') AS "Added at",
                    calories AS "Calories",
                    protein AS "Protein",
                    fat AS "Fat",
                    carbs AS "Carbohydrates",
                    meal AS "Meals or snacks"
            FROM nutrition  
            WHERE nutrition.user_id = %s AND "date" = %s
            ORDER BY entered_at DESC
            """

    logger.info("Executing query: %s with user_id %s and date %s",
                query, user_id, date)
    with self._database_connect() as connection:
        with connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query, (user_id, date))
            results = cursor.fetchall()
    
    daily_nutrition = [dict(result) for result in results]
    return daily_nutrition

def get_user_targets(self, username):
    user_id = self._find_user_id_by_username(username)
    query = """SELECT calorie_target, protein_target,
                        fat_target, carb_target
                FROM targets
                INNER JOIN users ON target_id = targets.id
                WHERE users.id = %s"""
    logger.info("Executing query: %s with user_id %s", query, user_id)
    with self._database_connect() as connection:
        with connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query, (user_id, ))
            user_targets = cursor.fetchone()
    return user_targets

def update_user_targets(self, username,
                        new_calorie_target, new_protein_target,
                        new_fat_target, new_carb_target):
    user_id = self._find_user_id_by_username(username)
    query = """
            UPDATE targets 
            SET calorie_target = %s,
                protein_target = %s,
                fat_target = %s,
                carb_target = %s
            WHERE id = (SELECT target_id FROM users
                        INNER JOIN targets ON target_id = targets.id
                        WHERE users.id = %s
                        )
            """
    logger.info("""Executing query: %s with
                %s as calorie_target,
                %s as protein_target,
                %s as fat_target,
                %s as carb_target,
                %s as user_id""" ,
                query, new_calorie_target, new_protein_target,
                new_fat_target, new_carb_target, user_id)
    
    with self._database_connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (new_calorie_target, new_protein_target,
                            new_fat_target, new_carb_target, user_id))
            
# Sum nutrition parameters for each day
def get_user_all_nutrition(self, username):
    user_id = self._find_user_id_by_username(username)
    query = """SELECT date,
                        SUM(calories) AS calories,
                        SUM(protein) AS protein, 
                        SUM(fat) AS fat,
                        SUM(carbs) AS carbs
            FROM users
            INNER JOIN nutrition ON user_id = users.id
            WHERE users.id = %s
            GROUP BY date
            ORDER BY date DESC
            """
    
    logger.info("Executing query: %s with user_id %s", query, user_id)
    with self._database_connect() as connection:
        with connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query, (user_id, ))
            results = cursor.fetchall()

    user_all_nutrition = [dict(result) for result in results]
    return user_all_nutrition

def add_nutrition_entry(self, date, username,
                        calories, protein, fat, carbs, meal):
    user_id = self._find_user_id_by_username(username)
    query_add_nutrition = """
        INSERT INTO nutrition 
                    (user_id, meal, date, calories, protein, fat, carbs)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    logger.info("""Executing query: %s with
                    user_id, meal, date, calories, protein, fat, carbs
                    %s, %s, %s, %s, %s, %s, %s""", 
                    query_add_nutrition, user_id, meal,
                    date, calories, protein, fat, carbs)
    with self._database_connect() as connection:
        with connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query_add_nutrition, (user_id, meal,
                    date, calories, protein, fat, carbs))

def find_nutrition_entry_by_id(self, nutrition_entry_id):
    query = """
            SELECT * FROM nutrition
            WHERE id = %s
            """
    logger.info("Executing query: %s with id %s", query, nutrition_entry_id)
    with self._database_connect() as connection:
        with connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query, (nutrition_entry_id, ))
            nutrition_entry = cursor.fetchone()

    return nutrition_entry

def update_nutrition_entry(self, nutrition_entry_id, calories,
                            protein, fat, carbs, meal):
    # meal_id = self.find_meal_id(meal)
    query = """
            UPDATE nutrition
            SET calories = %s, protein = %s, fat = %s,
                carbs = %s, meal = %s
            WHERE id = %s     
            """
    logger.info("""
                Executing query: %s with 
                calories, protein, fat, carbs, meal, id
                %s, %s, %s, %s, %s, %s""", 
                query, calories, protein, fat, carbs, meal,
                nutrition_entry_id)
    with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (calories, protein, fat, carbs,
                                        meal, nutrition_entry_id))

def delete_nutrition_entry(self, nutrition_entry_id):
    query = """
            DELETE FROM nutrition
            WHERE id = %s
            """
    logger.info("Executing query: %s with id %s", query,
                nutrition_entry_id)
    with self._database_connect() as connection:
        with connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query, (nutrition_entry_id, ))

def get_all_nutrition_entries_ids(self, username):
    user_id = self._find_user_id_by_username(username)
    query = '''
            SELECT id FROM nutrition
            WHERE user_id = %s
            '''
    logger.info("Executing query: %s with user_id %s", query, user_id)
    with self._database_connect() as connection:
        with connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query, (user_id, ))
            results = cursor.fetchall()
    
    nutrition_results = [dict(result) for result in results]
    all_nutrition_ids = []
    for item in nutrition_results:
        all_nutrition_ids.append(item['id'])
    return all_nutrition_ids