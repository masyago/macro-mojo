from contextlib import contextmanager

import bcrypt
import logging
import psycopg2
from psycopg2.extras import DictCursor

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
#Configure logging messages. Log INFO messages and higher severity messages
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class DatabasePersistence:
    
    @contextmanager
    def _database_connect(self):
        connection = psycopg2.connect(dbname='cal_tracker')
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
            is_password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_password)

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

        if not user_row: # test these two lines
            return None
        user_id = user_row['id']
        return user_id
    
    def daily_total_nutrition(self, username, date):
        user_id = self._find_user_id_by_username(username)

        query = """
                SELECT SUM(calories) AS calories, SUM(protein) as protein,
                       SUM(fat) AS fat, SUM(carbs) AS carbs
                FROM nutrition
                WHERE user_id = %s AND date = %s
                """
        logger.info("Executing query: %s with user_d %s and date %s", query, user_id, date)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, date))
                daily_total = cursor.fetchone()
        
        return daily_total
        
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
        logger.info("Executing query: %s with user_id %s and date %s", query, user_id, date)
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
                       TO_CHAR(entered_at, 'YYYY-MM-DD HH24:MI') AS "Added at",
                        calories AS "Calories",
                        protein AS "Protein",
                        fat AS "Fat",
                        carbs AS "Carbohydrates",
                        meals.name AS "Meals or snacks"
                FROM nutrition  
                INNER JOIN meals ON nutrition.meal_id = meals.id
                WHERE nutrition.user_id = %s AND "date" = %s
                ORDER BY entered_at DESC
                """
    
        logger.info("Executing query: %s with user_id %s and date %s", query, user_id, date)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, date))
                results = cursor.fetchall()
        
        daily_nutrition = [dict(result) for result in results]
        return daily_nutrition
    
    def get_user_targets(self, username):
        user_id = self._find_user_id_by_username(username)
        query = """SELECT calorie_target, protein_target, fat_target, carb_target
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
        query_meal_id = """
            SELECT id FROM meals
            WHERE name = %s
        """
        logger.info("Executing query: %s with name %s", query_meal_id, meal)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query_meal_id, (meal, ))
                result = cursor.fetchone()
        meal_id = result['id'] 

        query_add_nutrition = """
            INSERT INTO nutrition 
                        (user_id, meal_id, date, calories, protein, fat, carbs)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        logger.info("""Executing query: %s with
                        user_id, meal_id, date, calories, protein, fat, carbs
                        %s, %s, %s, %s, %s, %s, %s""", 
                        query_add_nutrition, user_id, meal_id,
                        date, calories, protein, fat, carbs)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query_add_nutrition, (user_id, meal_id,
                        date, calories, protein, fat, carbs))

    def find_nutrition_entry_by_id(self, username, nutrition_entry_id): # we can add user_id or username (with JOIN) 
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
        meal_id = self.find_meal_id(meal)
        query = """
                UPDATE nutrition
                SET calories = %s,
                    protein = %s,
                    fat = %s,
                    carbs = %s,
                    meal_id = %s
                WHERE id = %s     
                """
        logger.info("""
                    Executing query: %s with 
                    calories, protein, fat, carbs, meal_id, id
                    %s, %s, %s, %s, %s, %s""", 
                    query, calories, protein, fat, carbs, meal_id, nutrition_entry_id)
        with self._database_connect() as connection:
                with connection.cursor(cursor_factory=DictCursor) as cursor:
                    cursor.execute(query, (calories, protein, fat, carbs, meal_id, nutrition_entry_id))
            
    def find_meal_id(self, meal):
        query = """
                SELECT id FROM meals
                WHERE name = %s 
                """
        logger.info("Executing query: %s with meal %s", query, meal)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (meal, ))
                result = cursor.fetchone()
        
        meal_id = result['id']
        return meal_id
    
    def delete_nutrition_entry(self, nutrition_entry_id):
        query = """
                DELETE FROM nutrition
                WHERE id = %s
                """
        logger.info("Executing query: %s with id %s", query, nutrition_entry_id)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (nutrition_entry_id, ))

    def get_user_meals(self, username):
        user_id = self._find_user_id_by_username(username)
        query = '''
                SELECT * FROM meals
                WHERE user_id = %s
                ORDER BY name
                '''
        logger.info("Executing query: %s with user_id %s", query, user_id)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, ))
                results = cursor.fetchall()
        
        user_meals = [dict(result) for result in results]
        return user_meals
        
    def update_meal(self, username, meal_id, new_meal):
        user_id = self._find_user_id_by_username(username)
        query = '''
                UPDATE meals
                SET name = %s
                WHERE id = %s AND user_id = %s
                '''
        logger.info("Executing query: %s with name %s and id %s", query, new_meal, meal_id, user_id)
        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (new_meal, meal_id, user_id))

    def get_meal_data_by_id(self, meal_id):
        query = '''
                SELECT * FROM meals
                WHERE id = %s
                '''
        logger.info("Executing query: %s with id %s", query, meal_id)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (meal_id, ))
                meal_data = cursor.fetchone()

        return meal_data
    
    def delete_meal(self, meal_id):
        query = """
        DELETE FROM meals
        WHERE id = %s
        """
        logger.info("Executing query: %s with id %s", query, meal_id)
        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (meal_id, ))

    def add_meal(self, username, new_meal):
        user_id = self._find_user_id_by_username(username)
        query = """
                INSERT INTO meals (name, user_id)
                        VALUES (%s, %s)
                """
        logger.info("Executing query: %s with meal %s and user_id %s", query, new_meal, user_id)
        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (new_meal, user_id))

    def get_all_meal_names_except_current(self, username, meal_id):
        user_id = self._find_user_id_by_username(username)
        query = '''
                SELECT name FROM meals
                WHERE user_id = %s AND id != %s
                '''
        logger.info("Executing query: %s with user_id %s and id %s", query, user_id, meal_id)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, meal_id))
                results = cursor.fetchall()
        
        meal_names_no_current = [dict(result) for result in results]
        return meal_names_no_current
     
    def get_all_meal_names(self, username):
        user_id = self._find_user_id_by_username(username)
        query = '''
                SELECT name FROM meals
                WHERE user_id = %s
                '''
        logger.info("Executing query: %s with user_id %s", query, user_id)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, ))
                results = cursor.fetchall()
        
        meal_names = [dict(result) for result in results]
        return meal_names
    
    def get_all_meal_ids(self, username):
        user_id = self._find_user_id_by_username(username)
        query = '''
                SELECT id FROM meals
                WHERE user_id = %s
                '''
        logger.info("Executing query: %s with user_id %s", query, user_id)
        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, ))
                results = cursor.fetchall()
        
        meals_results = [dict(result) for result in results]
        all_meal_ids = []
        for item in meals_results:
            all_meal_ids.append(item['id'])
        return all_meal_ids
    
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

db_p = DatabasePersistence()
# print(db_p.get_all_meal_ids('test_user'))
print(db_p.get_all_nutrition_entries_ids('test_user'))

# # print(db_p.get_user_targets('test_user'))
# # print(db_p.get_daily_nutrition('test_user', '2025-07-28'))
# print(type(db_p._find_user_id_by_username('test_user')))
# # print(db_p.find_login('test_user', 'test_pwd'))
# print(db_p.get_user_all_nutrition('test_user'))

# print(db_p.find_meal_id('latte'))
