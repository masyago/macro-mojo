from contextlib import contextmanager

import bcrypt
import logging
import psycopg2
from psycopg2.extras import DictCursor

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
# Configure logging messages. Log INFO messages and higher severity messages
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class DatabasePersistence:
    @contextmanager
    def _database_connect(self):
        connection = psycopg2.connect(dbname='macro_mojo')
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def find_login(self, username, password):
        query = "SELECT * FROM users WHERE username = %s"
        logger.info("Executing query: %s with username %s", query, username)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (username, ))
                user_row = cursor.fetchone()

        if user_row:
            stored_password = user_row['hashed_pwd'].encode('utf-8')
            is_password_valid = bcrypt.checkpw(password.encode('utf-8'), 
                                               stored_password)
            if is_password_valid:
                return True
            
        return False
    
    def _find_user_id_by_username(self, username):
        query = "SELECT id FROM users WHERE username = %s"
        logger.info("Executing query: %s with username %s", query, username)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (username, ))
                user_row = cursor.fetchone()

        if not user_row:
            return None
        user_id = user_row['id']
        return user_id
    
    # Calculate sum of each nutrition parameter for specific date
    def daily_total_nutrition(self, username, date):
        user_id = self._find_user_id_by_username(username)
        query = """
                SELECT SUM(calories) AS calories, SUM(protein) as protein,
                       SUM(fat) AS fat, SUM(carbs) AS carbs
                FROM nutrition
                WHERE user_id = %s AND date = %s
                """
        logger.info("Executing query: %s with user_d %s and date %s", query,
                    user_id, date)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, date))
                daily_total = cursor.fetchone()
        
        return daily_total
    
    # Calculate leftover nutrition by subtracting sum from target
    def get_nutrition_left(self, username, date):
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
        logger.info("Executing query: %s with user_id %s and date %s",
                    query, user_id, date)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, date))
                nutrition_left = cursor.fetchone()
        return nutrition_left
    
    def get_daily_nutrition(self, username, date):
        user_id = self._find_user_id_by_username(username)
        # Get all nutrition data, including meals, for specific date
        query = """
                SELECT nutrition.id AS "nutrition_entry_id",
                       entered_at AS "Added at",
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