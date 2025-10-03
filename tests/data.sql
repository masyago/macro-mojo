INSERT INTO targets DEFAULT VALUES;
INSERT INTO targets DEFAULT VALUES;

INSERT INTO users (id, username, hashed_pwd, target_id)
VALUES (101, 'test_user',
    '$2b$12$944N3.hBdjR/X9XOXFGCC.m6yOXs1TjECJs/tSOIMEiL3t6DoHi0G', 1),
    (102, 'other', '$2b$12$nct0mkPNkvYJx8/fS7Kb3eqQ2ki9CNHwEDa2jqCQihWyiDBtjjVLu',
    2);

INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (101, '2025-09-02', 110, 4, 1, 21, 'ice cream');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (101, '2025-09-10', 300, 20, 15, 20, 'kebab');
INSERT INTO nutrition (user_id, date, calories, protein, fat, carbs, meal)
            VALUES (102, '2025-09-10', 50, 0, 0, 12, 'apple');

-- Password for 'other' is 'hello'