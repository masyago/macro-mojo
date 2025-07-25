INSERT INTO users (username, hashed_pwd)
        VALUES ('test_user', 'test_pwd');

INSERT INTO nutrition (user_id, calories)
       VALUES (1, 150);

INSERT INTO nutrition (user_id, calories)
       VALUES (1, 320);

INSERT INTO meals (name)
       VALUES ('yogurt'), ('apple');

UPDATE nutrition
SET meal_id = 1 
WHERE calories = 150;

UPDATE nutrition
SET meal_id = 2 
WHERE calories = 320;


SELECT username, SUM(calories) AS "Total calories today" FROM users  
INNER JOIN nutrition ON users.id = nutrition.user_id
GROUP BY username;  

SELECT DATE(entered_at) AS date,
                          SUM(calories) AS calories,
                          SUM(protein) AS protein, 
                          SUM(fat) AS fat,
                          SUM(carbs) AS carbs
                FROM users
                INNER JOIN nutrition ON user_id = users.id
                WHERE users.id = 1
                GROUP BY DATE(entered_at)
                ORDER BY DATE(entered_at);


INSERT INTO meals (name)
            VALUES ('waffle'), ('chicken burrito'),
                   ('apple'), ('salad'), ('smoothie');


INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-01');

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-02');
INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-06');
INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-10');
INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-13');
INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-16');
INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-21');
INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-22');
INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs, date)
VALUES (1, 15, 150, 20, 10, 12, '2025-06-30');


INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 25, 720, 20, 30, 12);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 12, 140, 12, 10, 0);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 26, 70, 0, 0, 10);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 20, 100, 0, 0, 25);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 25, 720, 20, 30, 12);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 12, 140, 12, 10, 0);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 26, 70, 0, 0, 10);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 20, 100, 0, 0, 25);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 25, 720, 20, 30, 12);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 12, 140, 12, 10, 0);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 26, 70, 0, 0, 10);

INSERT INTO nutrition (user_id, meal_id, calories, protein, fat, carbs)
VALUES (1, 20, 100, 0, 0, 25);