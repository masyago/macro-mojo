import os
import uuid
from pathlib import Path

import psycopg2
import pytest

# from app import app as flask_app

flask_app = None


def _run_sql_file(connection, path):
    with connection.cursor() as cursor, open(path, "r", encoding="utf-8") as file:
        cursor.execute(file.read())


"""
SETUP. For each session:
1. Create test database, set schema, and seed data. 
2. Drop database
"""


@pytest.fixture(scope="session")
def test_db_dsn():
    uuid_hex = uuid.uuid4().hex
    dbname = f"macro_mojo_test_{uuid_hex}"
    admin_connection = psycopg2.connect(dbname="postgres")
    admin_connection.autocommit = True

    """Create test database"""
    try:
        with admin_connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE {dbname}")
    finally:
        admin_connection.close()

    """Get aboslute pathes for files containing schema and seed data"""
    # Get an absolute path for a project folder (parent directory)
    project_root = Path(__file__).resolve().parents[1]
    schema_path = project_root / "schema.sql"
    # Get an absolute path for current, `tests`, directory
    tests_directory = Path(__file__).resolve().parent
    data_path = tests_directory / "data.sql"

    """Create schema and load seed data to test database"""
    dsn = f"dbname={dbname}"
    with psycopg2.connect(dsn) as connection:
        connection.autocommit = True
        _run_sql_file(connection, schema_path)
        _run_sql_file(connection, data_path)

    yield dsn

    """TEARDOWN: 
    1. Block new connections and terminate existing connections to the database
    2. Drop test database
    3. Close the connection to postgres
    """
    admin_connection = psycopg2.connect(dbname="postgres")
    admin_connection.autocommit = True
    try:
        with admin_connection.cursor() as cursor:
            # Block new connections
            cursor.execute(
                """
                        UPDATE pg_database SET datallowconn = false
                        WHERE datname = %s""",
                (dbname,),
            )
            # Terminate existing sessions
            cursor.execute(
                """SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity WHERE datname = %s""",
                (dbname,),
            )
            # Drop the database
            cursor.execute(f"DROP DATABASE {dbname}")
    finally:
        admin_connection.close()


@pytest.fixture
def app(test_db_dsn, monkeypatch):
    # Import app in fixutre to avoid import failures if app.py has issues
    import app as app_module

    # Change database to test database
    monkeypatch.setenv("DATABASE_URL", test_db_dsn)
    app_module.app.config.update(TESTING=True)
    yield app_module.app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
