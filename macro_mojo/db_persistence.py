from contextlib import contextmanager

import bcrypt
import logging
import psycopg2
from psycopg2.extras import DictCursor
from typing import List, Optional, Any, Iterator, Dict

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
# Configure logging messages. Log INFO messages and higher severity messages
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class DatabasePersistence:
    def __init__(self, dsn: Optional[str] = None) -> None:
        # `dsn` is 'data source name'
        self._dsn = dsn

    @contextmanager
    def _database_connect(self) -> Iterator[psycopg2.extensions.connection]:
        """
        Open a PostgreSQL connection.
        Uses explicit DSN if provided; otherwise falls back to environment or
        default.
        """
        logger.info(
            "Connecting to database using %s",
            "DSN" if self._dsn else "default dbname=macro_mojo",
        )
        connection = (
            psycopg2.connect(self._dsn)
            if self._dsn
            else psycopg2.connect(dbname="macro_mojo")
        )
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def find_login(self, username: str, password: str) -> bool:
        query = "SELECT * FROM users WHERE username = %s"
        logger.info("Executing query: %s with username %s", query, username)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (username,))
                user_row = cursor.fetchone()

        if user_row:
            stored_password = user_row["hashed_pwd"].encode("utf-8")
            is_password_valid = bcrypt.checkpw(
                password.encode("utf-8"), stored_password
            )
            if is_password_valid:
                return True

        return False

    def _find_user_id_by_username(self, username: str) -> Optional[int]:
        query = "SELECT id FROM users WHERE username = %s"
        logger.info("Executing query: %s with username %s", query, username)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (username,))
                user_row = cursor.fetchone()

        if not user_row:
            return None
        user_id = user_row["id"]
        return user_id

    # Calculate sum of each nutrition parameter for specific date
    def daily_total_nutrition(
        self, username: str, date: str
    ) -> Optional[Dict[str, Any]]:
        user_id = self._find_user_id_by_username(username)
        query = """
                SELECT SUM(calories) AS calories, SUM(protein) as protein,
                       SUM(fat) AS fat, SUM(carbs) AS carbs
                FROM nutrition
                WHERE user_id = %s AND date = %s
                """
        logger.info(
            "Executing query: %s with user_d %s and date %s",
            query,
            user_id,
            date,
        )
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, date))
                daily_total = cursor.fetchone()

        return daily_total

    # Calculate leftover nutrition by subtracting sum from target
    def get_nutrition_left(
        self, username: str, date: str
    ) -> Optional[Dict[str, Any]]:
        user_id = self._find_user_id_by_username(username)
        query = """
                SELECT (calorie_target - SUM(calories)) AS "Calories left",
                       (protein_target - SUM(protein)) AS "Protein left",
                       (fat_target - SUM(fat)) AS "Fat left",
                       (carb_target - SUM(carbs)) AS "Carbs left"
                FROM users 
                LEFT OUTER JOIN targets ON target_id = targets.id
                LEFT OUTER JOIN nutrition ON nutrition.user_id = users.id
                WHERE user_id = %s AND date = %s
                GROUP BY targets.id 
                """
        logger.info(
            "Executing query: %s with user_id %s and date %s",
            query,
            user_id,
            date,
        )
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, date))
                nutrition_left = cursor.fetchone()
        return nutrition_left

    def get_daily_nutrition(
        self, username: str, date: str
    ) -> List[Dict[str, Any]]:
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

        logger.info(
            "Executing query: %s with user_id %s and date %s",
            query,
            user_id,
            date,
        )
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, date))
                results = cursor.fetchall()

        daily_nutrition = [dict(result) for result in results]
        return daily_nutrition

    def get_user_targets(self, username: str) -> Optional[Dict[str, Any]]:
        user_id = self._find_user_id_by_username(username)
        query = """SELECT calorie_target, protein_target,
                          fat_target, carb_target
                   FROM targets
                   INNER JOIN users ON target_id = targets.id
                   WHERE users.id = %s"""
        logger.info("Executing query: %s with user_id %s", query, user_id)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id,))
                user_targets = cursor.fetchone()
        return user_targets

    def update_user_targets(
        self,
        username: str,
        new_calorie_target: str,  # New targets come from HTML forms as str
        new_protein_target: str,
        new_fat_target: str,
        new_carb_target: str,
    ) -> None:
        user_id = self._find_user_id_by_username(username)

        # Convert str to int before database insertion
        calorie_int = int(new_calorie_target)
        protein_int = int(new_protein_target)
        fat_int = int(new_fat_target)
        carb_int = int(new_carb_target)

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
        logger.info(
            """Executing query: %s with
                    %s as calorie_target,
                    %s as protein_target,
                    %s as fat_target,
                    %s as carb_target,
                    %s as user_id""",
            query,
            new_calorie_target,
            new_protein_target,
            new_fat_target,
            new_carb_target,
            user_id,
        )

        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        calorie_int,
                        protein_int,
                        fat_int,
                        carb_int,
                        user_id,
                    ),
                )

    # Sum nutrition parameters for each day
    def get_user_all_nutrition(self, username: str) -> List[Dict[str, Any]]:
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
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()

        user_all_nutrition = [dict(result) for result in results]
        return user_all_nutrition

    def add_nutrition_entry(
        self,
        date: str,
        username: str,
        calories: str,  # Values come from HTML forms as str
        protein: str,
        fat: str,
        carbs: str,
        meal: str,
    ) -> None:
        user_id = self._find_user_id_by_username(username)

        # Convert str to int before database insertion
        calorie_int = int(calories)
        protein_int = int(protein)
        fat_int = int(fat)
        carb_int = int(carbs)

        query_add_nutrition = """
            INSERT INTO nutrition 
                        (user_id, meal, date, calories, protein, fat, carbs)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        logger.info(
            """Executing query: %s with
                        user_id, meal, date, calories, protein, fat, carbs
                        %s, %s, %s, %s, %s, %s, %s""",
            query_add_nutrition,
            user_id,
            meal,
            date,
            calories,
            protein,
            fat,
            carbs,
        )
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(
                    query_add_nutrition,
                    (
                        user_id,
                        meal,
                        date,
                        calorie_int,
                        protein_int,
                        fat_int,
                        carb_int,
                    ),
                )

    def find_nutrition_entry_by_id(
        self, nutrition_entry_id: int
    ) -> Optional[Dict[str, Any]]:
        query = """
                SELECT * FROM nutrition
                WHERE id = %s
                """
        logger.info(
            "Executing query: %s with id %s", query, nutrition_entry_id
        )
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (nutrition_entry_id,))
                nutrition_entry = cursor.fetchone()

        return nutrition_entry

    def update_nutrition_entry(
        self,
        nutrition_entry_id: int,
        calories: str,
        protein: str,
        fat: str,
        carbs: str,
        meal: str,
    ) -> None:

        # Convert str to int before database insertion
        calorie_int = int(calories)
        protein_int = int(protein)
        fat_int = int(fat)
        carb_int = int(carbs)

        query = """
                UPDATE nutrition
                SET calories = %s, protein = %s, fat = %s,
                    carbs = %s, meal = %s
                WHERE id = %s     
                """
        logger.info(
            """
                    Executing query: %s with 
                    calories, protein, fat, carbs, meal, id
                    %s, %s, %s, %s, %s, %s""",
            query,
            calories,
            protein,
            fat,
            carbs,
            meal,
            nutrition_entry_id,
        )
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(
                    query,
                    (
                        calorie_int,
                        protein_int,
                        fat_int,
                        carb_int,
                        meal,
                        nutrition_entry_id,
                    ),
                )

    def delete_nutrition_entry(self, nutrition_entry_id: int) -> None:
        query = """
                DELETE FROM nutrition
                WHERE id = %s
                """
        logger.info(
            "Executing query: %s with id %s", query, nutrition_entry_id
        )
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (nutrition_entry_id,))

    def get_all_nutrition_entries_ids(self, username: str) -> List[int]:
        user_id = self._find_user_id_by_username(username)
        query = """
                SELECT id FROM nutrition
                WHERE user_id = %s
                """
        logger.info("Executing query: %s with user_id %s", query, user_id)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()

        nutrition_results = [dict(result) for result in results]
        all_nutrition_ids = []
        for item in nutrition_results:
            all_nutrition_ids.append(item["id"])
        return all_nutrition_ids
