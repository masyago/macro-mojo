INSERT INTO targets DEFAULT VALUES;

INSERT INTO users (id, username, hashed_pwd, target_id)
        VALUES (1, 'test_user',
        '$2b$12$944N3.hBdjR/X9XOXFGCC.m6yOXs1TjECJs/tSOIMEiL3t6DoHi0G', 1);

-- INSERT INTO meals (name, user_id)
--             VALUES ('waffle', 1), ('chicken burrito', 1),
--                    ('apple', 1), ('salad', 1), ('smoothie', 1),
--                    ('PB&J', 1), ('yogurt bowl', 1), ('pizza 1 slice', 1),
--                    ('protein bar', 1);

INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-06-02', 250, 3, 5, 40, 'waffle');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-06-10', 300, 5, 20, 20, 'salad');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-06-10', 285, 12, 10, 36, 'chicken burrito');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-06-17', 100, 0, 0, 25, 'apple');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-06-25', 380, 12, 18, 46, 'smoothie');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-07-25', 415, 24, 3, 70, 'PB&J');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-07-28', 550, 30, 14, 78, 'chicken burrito');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-07-28', 500, 6, 10, 80, 'pizza 1 slice');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-07-28', 285, 12, 10, 36, 'chicken burrito');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-07-28', 50, 0, 0, 12, 'apple');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-07-28', 290, 17, 10, 35, 'yogurt bowl');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (1, '2025-07-28', 180, 21, 5, 5, 'protein bar');
