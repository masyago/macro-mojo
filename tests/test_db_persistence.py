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
Pytest fixture creates a new DatabasePersistence instance for each test.
Scoped to functions (default scope)
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
    hashed_pwd = bcrypt.hashpw(
        "hungry".encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
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
    query, parameters = cursor.executed[0]
    assert "FROM users" in query
    assert parameters == ("cat",)


def test_find_login_wrong_password(dp):
    hashed_pwd = bcrypt.hashpw(
        "hungry".encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    cursor = FakeCursor(fetchone_result={"hashed_pwd": hashed_pwd})
    with patch_connect(dp, cursor):
        # Call `find_login` using fake cursor. Returns `False` when password
        # is not correct
        find_login_result = dp.find_login("cat", "not_hungry")
    assert find_login_result is False


def test_find_login_wrong_username(dp):
    cursor = FakeCursor(fetchone_result=None)
    with patch_connect(dp, cursor):
        # Call `find_login` using fake cursor. Returns `False` if username
        # not found
        find_login_result = dp.find_login("snake", "hungry")
    assert find_login_result is False


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
    expected_daily_total = {
        "calories": 1000,
        "protein": 34,
        "fat": 11,
        "carbs": 191,
    }
    cursor = FakeCursor(fetchone_result=expected_daily_total)

    # Replace helper method `_find_user_id_by_username` with a spy that takes
    # username as argument and returns `id` value
    captured_username = {}

    def fake_id_lookup(username):
        captured_username["value"] = username
        return 6

    monkeypatch.setattr(dp, "_find_user_id_by_username", fake_id_lookup)

    with patch_connect(dp, cursor):
        test_result = dp.daily_total_nutrition("Mike", "2025-09-14")
    assert test_result == expected_daily_total
    assert captured_username["value"] == "Mike"
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT SUM(calories)" in query
    assert parameters == (6, "2025-09-14")


def test_daily_total_nutrition_no_rows(dp, monkeypatch):
    cursor = FakeCursor(fetchone_result=None)
    monkeypatch.setattr(dp, "_find_user_id_by_username", lambda username: 5)

    with patch_connect(dp, cursor):
        test_result = dp.daily_total_nutrition("Mike", "2025-03-14")
    assert test_result is None
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT SUM(calories)" in query
    assert parameters == (5, "2025-03-14")


"""
Tests for method `get_nutrition_left.
1. Check that the method returns correct `nutrition_left` when provided 
   username and date
2. Returns `None` if rows with the specified date not found
"""


def test_get_nutrition_left_ok(dp, monkeypatch):
    expected_nutrition_left = {
        "Calories left": 500,
        "Protein left": 30,
        "Fat left": 11,
        "Carbs left": 10,
    }
    cursor = FakeCursor(fetchone_result=expected_nutrition_left)

    captured_username = {}

    def fake_id_lookup(username):
        captured_username["value"] = username
        return 6

    monkeypatch.setattr(dp, "_find_user_id_by_username", fake_id_lookup)

    with patch_connect(dp, cursor):
        test_result = dp.get_nutrition_left("Mike", "2025-09-14")

    assert test_result == expected_nutrition_left
    assert captured_username["value"] == "Mike"
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT (calorie_target - SUM(calories))" in query
    assert "LEFT OUTER JOIN targets ON target_id" in query
    assert "LEFT OUTER JOIN nutrition ON nutrition" in query
    assert parameters == (6, "2025-09-14")


def test_get_nutrition_left_no_rows(dp, monkeypatch):
    cursor = FakeCursor(fetchone_result=None)
    monkeypatch.setattr(dp, "_find_user_id_by_username", lambda username: 6)

    with patch_connect(dp, cursor):
        test_result = dp.get_nutrition_left("Mike", "2025-03-14")
    assert test_result is None
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT (calorie_target - SUM(calories))" in query
    assert parameters == (6, "2025-03-14")


"""
Tests for method `get_daily_nutrition`. 2 scenarios: with result row and when
result row is None
Note: Switched to pytest parametrization to avoid code repetition.
"""


@pytest.mark.parametrize(
    "username, date, user_id, fetchall_rows, expected",
    [
        (
            "Mike",
            "2025-09-14",
            6,
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
                },
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
                },
            ],
        ),
        ("Mike", "2025-09-14", 6, [], []),
    ],
    ids=["daily_nutrition_with_rows", "daily_nutrition_no_rows"],
)
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


"""
Tests for method `get_user_targets`: with and without existing targets.
"""


@pytest.mark.parametrize(
    "username, user_id, fetchone_result, expected",
    [
        (
            "Mike",
            6,
            {
                "calorie_target": 2000,
                "protein_target": 100,
                "fat_target": 60,
                "carb_target": 260,
            },
            {
                "calorie_target": 2000,
                "protein_target": 100,
                "fat_target": 60,
                "carb_target": 260,
            },
        ),
        ("Jess", 7, None, None),
    ],
    ids=["user_targets_exist", "user_targets_dont_exist"],
)
def test_get_user_targets(
    dp, monkeypatch, username, user_id, fetchone_result, expected
):
    # mock find_user_by_if using mmonekypatch and lambda
    # use fake cursor and face connection to execute the query
    # assert
    cursor = FakeCursor(fetchone_result=fetchone_result)
    monkeypatch.setattr(dp, "_find_user_id_by_username", lambda u: user_id)

    with patch_connect(dp, cursor):
        result = dp.get_user_targets(username)

    assert result == expected
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT calorie_target" in query
    assert "FROM targets" in query
    assert parameters == (user_id,)


"""
Tests for the method `update_user_targets`
"""


def test_update_user_targets_ok(dp, monkeypatch):
    cursor = FakeCursor()

    captured_username = {}

    def fake_id_lookup(username):
        captured_username["value"] = username
        return 6

    monkeypatch.setattr(dp, "_find_user_id_by_username", fake_id_lookup)

    with patch_connect(dp, cursor):
        dp.update_user_targets("Mike", 1500, 100, 10, 300)

    assert captured_username["value"] == "Mike"
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "UPDATE targets " in query
    assert parameters == (1500, 100, 10, 300, 6)


""" Tests for the method `get_user_all_nutrition`. Cases:
1. Nutrition entries for the username exist
2. No nutrition entries found for the username
"""


@pytest.mark.parametrize(
    "username, user_id, fetchall_result, expected",
    [
        (
            "Mike",
            6,
            [
                {
                    "date": "2025-06-15",
                    "calories": 2001,
                    "protein": 115,
                    "fat": 65,
                    "carbs": 250,
                },
                {
                    "date": "2025-02-17",
                    "calories": 2000,
                    "protein": 110,
                    "fat": 60,
                    "carbs": 252,
                },
            ],
            [
                {
                    "date": "2025-06-15",
                    "calories": 2001,
                    "protein": 115,
                    "fat": 65,
                    "carbs": 250,
                },
                {
                    "date": "2025-02-17",
                    "calories": 2000,
                    "protein": 110,
                    "fat": 60,
                    "carbs": 252,
                },
            ],
        ),
        ("Mike", 6, [], []),
    ],
    ids=["user_all_nutrition_with_rows", "user_all_nutrition_no_rows"],
)
def test_get_user_all_nutrition(
    dp, monkeypatch, username, user_id, fetchall_result, expected
):

    cursor = FakeCursor(fetchall_result=fetchall_result)
    monkeypatch.setattr(dp, "_find_user_id_by_username", lambda u: user_id)

    with patch_connect(dp, cursor):
        result = dp.get_user_all_nutrition(username)

    assert result == expected
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT date" in query
    assert "SUM(calories)" in query
    assert parameters == (6,)


"""
Tests for the method `add_nutrition_entry`.
"""


def test_add_nutrition_entry(dp, monkeypatch):
    cursor = FakeCursor()

    captured_username = {}

    def fake_id_lookup(username):
        captured_username["value"] = username
        return 6

    monkeypatch.setattr(dp, "_find_user_id_by_username", fake_id_lookup)

    with patch_connect(dp, cursor):
        dp.add_nutrition_entry(
            "2025-06-24", "Mike", 500, 50, 20, 25, "chicken bowl"
        )

    assert captured_username["value"] == "Mike"
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "INSERT INTO nutrition" in query
    assert parameters == (6, "chicken bowl", "2025-06-24", 500, 50, 20, 25)


"""
Tests for the `find_nutrition_entry_by_id`. Cases: 
- nutrition_entry_id is found
- nutrition_entry_id is not found
"""


@pytest.mark.parametrize(
    "nutrition_entry_id, nutrition_entry_result, expected",
    [
        (
            10,
            {
                "id": 10,
                "user_id": 6,
                "date": "2025-10-01",
                "entered_at": "2025-10-01 10:12:15.789123",
                "calories": 180,
                "protein": 21,
                "fat": 5,
                "carbs": 3,
                "meal": "protein bar",
            },
            {
                "id": 10,
                "user_id": 6,
                "date": "2025-10-01",
                "entered_at": "2025-10-01 10:12:15.789123",
                "calories": 180,
                "protein": 21,
                "fat": 5,
                "carbs": 3,
                "meal": "protein bar",
            },
        ),
        (
            10412,
            None,
            None,
        ),
    ],
    ids=["nutrition_entry_id_exists", "nutrition_entry_doesnt_exist"],
)
def test_find_nutrition_entry_by_id(
    dp, nutrition_entry_id, nutrition_entry_result, expected
):
    cursor = FakeCursor(fetchone_result=nutrition_entry_result)

    with patch_connect(dp, cursor):
        result = dp.find_nutrition_entry_by_id(nutrition_entry_id)

    assert result == expected
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT * FROM nutrition" in query
    assert parameters == (nutrition_entry_id,)


"""
Tests for `update_nutrition_entry`
"""


def test_update_nutrition_entry(dp):
    cursor = FakeCursor()

    with patch_connect(dp, cursor):
        dp.update_nutrition_entry(104, 1500, 40, 70, 177, "pasta")

    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "UPDATE nutrition" in query
    assert parameters == (1500, 40, 70, 177, "pasta", 104)


"""
Tests for `delete_nutrition_entry`
"""


def test_delete_nutrition_entry(dp):
    cursor = FakeCursor()
    nutrition_entry_id = 104

    with patch_connect(dp, cursor):
        dp.delete_nutrition_entry(nutrition_entry_id)

    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "DELETE FROM nutrition" in query
    assert parameters == (104,)


"""
Tests for `get_all_nutrition_entries_ids`. Cases:
- some nutrition id's exist
- nutrition ids don't exist
"""


@pytest.mark.parametrize(
    "username, user_id, fetchall_result, expected",
    [
        (
            "Mike",
            6,
            [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 45}],
            [1, 2, 3, 45],
        ),
        ("Sophia", 11, [], []),
    ],
    ids=[
        "all_nutrition_entries_ids_some_values",
        "all_nutrition_entries_ids_dont_exist",
    ],
)
def test_get_all_nutrition_entries_ids(
    dp, monkeypatch, username, user_id, fetchall_result, expected
):
    cursor = FakeCursor(fetchall_result=fetchall_result)

    captured_username = {}

    def fake_id_lookup(username):
        captured_username["value"] = username
        return user_id

    monkeypatch.setattr(dp, "_find_user_id_by_username", fake_id_lookup)

    with patch_connect(dp, cursor):
        result_id_list = dp.get_all_nutrition_entries_ids(username)

    assert captured_username["value"] == username
    assert result_id_list == expected
    assert len(cursor.executed) == 1
    query, parameters = cursor.executed[0]
    assert "SELECT id FROM nutrition" in query
    assert parameters == (user_id,)
