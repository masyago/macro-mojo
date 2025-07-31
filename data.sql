INSERT INTO targets DEFAULT VALUES;

INSERT INTO users (id, username, hashed_pwd, target_id)
        VALUES (1, 'test_user', '$2b$12$944N3.hBdjR/X9XOXFGCC.m6yOXs1TjECJs/tSOIMEiL3t6DoHi0G', 1);

INSERT INTO meals (name, user_id)
            VALUES ('waffle', 1), ('chicken burrito', 1),
                   ('apple', 1), ('salad', 1), ('smoothie', 1),
                   ('PB&J', 1), ('yogurt bowl', 1), ('pizza 1 slice', 1),
                   ('protein bar', 1);

INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 1, '2025-06-02', 250, 3, 5, 40);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 4, '2025-06-10', 300, 5, 20, 20);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 8, '2025-06-10', 285, 12, 10, 36);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 3, '2025-06-17', 100, 0, 0, 25);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 6, '2025-06-25', 380, 12, 18, 46);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 5, '2025-07-25', 415, 24, 3, 70);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 2, '2025-07-28', 550, 30, 14, 78);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 1, '2025-07-28', 500, 6, 10, 80);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 8, '2025-07-28', 285, 12, 10, 36);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 3, '2025-07-28', 50, 0, 0, 12);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 7, '2025-07-28', 290, 17, 10, 35);
INSERT INTO nutrition (user_id, meal_id, date, calories, protein, fat, carbs)
            VALUES (1, 9, '2025-07-28', 180, 21, 5, 5);
