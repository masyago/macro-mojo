CREATE TABLE users (
    id serial PRIMARY KEY,
    username text NOT NULL UNIQUE,
    hashed_pwd text NOT NULL,
    target_id integer UNIQUE NOT NULL REFERENCES targets(id) 
                      ON DELETE CASCADE
);

CREATE TABLE targets (
    id serial PRIMARY KEY,
    calorie_target integer NOT NULL DEFAULT 2000,
    protein_target integer NOT NULL DEFAULT 100,
    fat_target integer NOT NULL DEFAULT 60,
    carb_target integer NOT NULL DEFAULT 265
);

CREATE TABLE nutrition (
    id serial PRIMARY KEY,
    user_id integer NOT NULL REFERENCES users(id)
                             ON DELETE CASCADE,
    meal_id integer NOT NULL REFERENCES meals(id)
                             ON DELETE CASCADE,
    "date" date NOT NULL DEFAULT NOW(),
    entered_at timestamp NOT NULL DEFAULT NOW(),
    calories integer NOT NULL,
    protein integer NOT NULL,
    fat integer NOT NULL,
    carbs integer NOT NULL
);

CREATE TABLE meals (
    id serial PRIMARY KEY,
    name text UNIQUE NOT NULL
);



#### For set up only - DELETE #####
ALTER TABLE targets
ALTER COLUMN calorie_target
SET DEFAULT 2000;

ALTER TABLE targets
ALTER COLUMN calorie_target
SET NOT NULL;


ALTER TABLE targets
ALTER COLUMN protein_target
SET DEFAULT 100;

ALTER TABLE targets
ALTER COLUMN protein_target
SET NOT NULL;


ALTER TABLE targets
ALTER COLUMN fat_target 
SET DEFAULT 60;

ALTER TABLE targets
ALTER COLUMN fat_target 
SET NOT NULL;

ALTER TABLE targets
ALTER COLUMN carb_target 
SET DEFAULT 265;

ALTER TABLE targets
ALTER COLUMN carb_target 
SET NOT NULL;

### nutrition table ###

DELETE FROM nutrition
WHERE meal_id IS NULL;

DELETE FROM nutrition
WHERE protein IS NULL;

DELETE FROM nutrition
WHERE fat IS NULL;

DELETE FROM nutrition
WHERE carbs IS NULL;


ALTER TABLE nutrition
ALTER COLUMN meal_id
SET NOT NULL;

ALTER TABLE nutrition
ALTER COLUMN protein
SET NOT NULL;

ALTER TABLE nutrition
ALTER COLUMN fat
SET NOT NULL;

ALTER TABLE nutrition
ALTER COLUMN carbs
SET NOT NULL;


#### meals ####

SELECT name FROM meals
GROUP BY name
HAVING count(name) > 1;

DELETE FROM meals
WHERE name IN (
    SELECT name FROM meals
    GROUP BY name
    HAVING count(name) > 1
);

INSERT INTO meals (name)
VALUES ('latte'), ('burger'), ('apple'), ('yogurt bowl');

ALTER TABLE meals
ADD CONSTRAINT unique_meal UNIQUE (name);
