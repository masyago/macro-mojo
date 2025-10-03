CREATE TABLE targets (
    id serial PRIMARY KEY,
    calorie_target integer NOT NULL DEFAULT 2000,
    protein_target integer NOT NULL DEFAULT 100,
    fat_target integer NOT NULL DEFAULT 60,
    carb_target integer NOT NULL DEFAULT 265
);

CREATE TABLE users (
    id serial PRIMARY KEY,
    username text NOT NULL UNIQUE,
    hashed_pwd text NOT NULL,
    target_id integer UNIQUE NOT NULL REFERENCES targets(id) 
                                      ON DELETE CASCADE
);

CREATE TABLE nutrition (
    id serial PRIMARY KEY,
    user_id integer NOT NULL REFERENCES users(id)
                             ON DELETE CASCADE,
    "date" date NOT NULL DEFAULT NOW(),
    entered_at timestamp NOT NULL DEFAULT NOW(),
    calories integer NOT NULL,
    protein integer NOT NULL,
    fat integer NOT NULL,
    carbs integer NOT NULL,
    meal text
);