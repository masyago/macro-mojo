import importlib
from unittest.mock import patch
from contextlib import contextmanager
import bcrypt
import pytest

try:
    dbp_module = importlib.import_module("macro_mojo.db_persistence")
    DatabasePersistence = dbp_module.DatabasePersistence
except ModuleNotFoundError:
    pytest.skip("macro_mojo.db_persistence not available", allow_module_level=True)


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self, cursor_factory=None):
        return self._cursor


@pytest.fixture
def dp():
    return DatabasePersistence(dsn="fake-dsn")


def patch_connect(dp, cursor: FakeCursor):
    @contextmanager
    def fake_connect():
        yield FakeConnection(cursor)
    return patch.object(dp, "_database_connect", fake_connect)


# find_login
def test_find_login_success(dp):
    hashed = bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode("utf-8")
    cursor = FakeCursor(fetchone_result={"hashed_pwd": hashed})
    with patch_connect(dp, cursor):
        ok = dp.find_login("alice", "secret")
    assert ok is True
    assert len(cursor.executed) == 1
    q, p = cursor.executed[0]
    assert "FROM users" in q
    assert p == ("alice",)


def test_find_login_wrong_password(dp):
    hashed = bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode("utf-8")
    cursor = FakeCursor(fetchone_result={"hashed_pwd": hashed})
    with patch_connect(dp, cursor):
        ok = dp.find_login("alice", "nope")
    assert ok is False


def test_find_login_user_missing(dp):
    cursor = FakeCursor(fetchone_result=None)
    with patch_connect(dp, cursor):
        ok = dp.find_login("ghost", "secret")
    assert ok is False


# _find_user_id_by_username
def test_find_user_id_by_username_found(dp):
    cursor = FakeCursor(fetchone_result={"id": 7})
    with patch_connect(dp, cursor):
        uid = dp._find_user_id_by_username("alice")
    assert uid == 7


def test_find_user_id_by_username_not_found(dp):
    cursor = FakeCursor(fetchone_result=None)
    with patch_connect(dp, cursor):
        uid = dp._find_user_id_by_username("none")
    assert uid is None


# daily_total_nutrition
def test_daily_total_nutrition(dp):
    expected = {"calories": 1200, "protein": 90, "fat": 40, "carbs": 150}
    cursor = FakeCursor(fetchone_result=expected)
    with patch.object(dp, "_find_user_id_by_username", return_value=5), \
         patch_connect(dp, cursor):
        result = dp.daily_total_nutrition("alice", "2024-01-01")
    assert result == expected
    assert len(cursor.executed) == 1


# get_nutrition_left
def test_get_nutrition_left(dp):
    expected = {"Calories left": 800, "Protein left": 30, "Fat left": 20, "Carbs left": 100}
    cursor = FakeCursor(fetchone_result=expected)
    with patch.object(dp, "_find_user_id_by_username", return_value=3), \
         patch_connect(dp, cursor):
        result = dp.get_nutrition_left("alice", "2024-01-02")
    assert result == expected


# get_daily_nutrition
def test_get_daily_nutrition(dp):
    rows = [
        {"nutrition_entry_id": 2, "Added at": "08:00 AM", "Calories": 400,
         "Protein": 30, "Fat": 10, "Carbohydrates": 50, "Meals or snacks": "Breakfast"},
        {"nutrition_entry_id": 1, "Added at": "12:00 PM", "Calories": 600,
         "Protein": 40, "Fat": 20, "Carbohydrates": 70, "Meals or snacks": "Lunch"},
    ]
    cursor = FakeCursor(fetchall_result=rows)
    with patch.object(dp, "_find_user_id_by_username", return_value=9), \
         patch_connect(dp, cursor):
        result = dp.get_daily_nutrition("alice", "2024-01-03")
    assert result == rows
    assert len(result) == 2


# get_user_targets
def test_get_user_targets(dp):
    row = {"calorie_target": 2000, "protein_target": 150, "fat_target": 70, "carb_target": 210}
    cursor = FakeCursor(fetchone_result=row)
    with patch.object(dp, "_find_user_id_by_username", return_value=11), \
         patch_connect(dp, cursor):
        result = dp.get_user_targets("alice")
    assert result == row


# update_user_targets
def test_update_user_targets(dp):
    cursor = FakeCursor()
    with patch.object(dp, "_find_user_id_by_username", return_value=11), \
         patch_connect(dp, cursor):
        dp.update_user_targets("alice", 1800, 140, 60, 190)
    assert len(cursor.executed) == 1
    q, params = cursor.executed[0]
    assert "UPDATE targets" in q
    assert params == (1800, 140, 60, 190, 11)


# get_user_all_nutrition
def test_get_user_all_nutrition(dp):
    rows = [
        {"date": "2024-02-02", "calories": 2200, "protein": 160, "fat": 80, "carbs": 250},
        {"date": "2024-02-01", "calories": 2000, "protein": 150, "fat": 70, "carbs": 230},
    ]
    cursor = FakeCursor(fetchall_result=rows)
    with patch.object(dp, "_find_user_id_by_username", return_value=12), \
         patch_connect(dp, cursor):
        result = dp.get_user_all_nutrition("alice")
    assert result == rows


# add_nutrition_entry
def test_add_nutrition_entry(dp):
    cursor = FakeCursor()
    with patch.object(dp, "_find_user_id_by_username", return_value=77), \
         patch_connect(dp, cursor):
        dp.add_nutrition_entry("2024-03-01", "alice", 500, 40, 15, 60, "Snack")
    assert len(cursor.executed) == 1
    q, params = cursor.executed[0]
    assert "INSERT INTO nutrition" in q
    assert params == (77, "Snack", "2024-03-01", 500, 40, 15, 60)


# find_nutrition_entry_by_id
def test_find_nutrition_entry_by_id(dp):
    row = {"id": 5, "calories": 300}
    cursor = FakeCursor(fetchone_result=row)
    with patch_connect(dp, cursor):
        result = dp.find_nutrition_entry_by_id(5)
    assert result == row


# update_nutrition_entry
def test_update_nutrition_entry(dp):
    cursor = FakeCursor()
    with patch_connect(dp, cursor):
        dp.update_nutrition_entry(9, 450, 35, 12, 55, "Dinner")
    assert len(cursor.executed) == 1
    q, params = cursor.executed[0]
    assert "UPDATE nutrition" in q
    assert params == (450, 35, 12, 55, "Dinner", 9)


# delete_nutrition_entry
def test_delete_nutrition_entry(dp):
    cursor = FakeCursor()
    with patch_connect(dp, cursor):
        dp.delete_nutrition_entry(10)
    assert len(cursor.executed) == 1
    q, params = cursor.executed[0]
    assert "DELETE FROM nutrition" in q
    assert params == (10,)


# get_all_nutrition_entries_ids
def test_get_all_nutrition_entries_ids(dp):
    rows = [{"id": 1}, {"id": 2}, {"id": 3}]
    cursor = FakeCursor(fetchall_result=rows)
    with patch.object(dp, "_find_user_id_by_username", return_value=33), \
         patch_connect(dp, cursor):
        ids = dp.get_all_nutrition_entries_ids("alice")
    assert ids == [1, 2, 3]
