CREATE DATABASE imdb_reviews;
\connect imdb_reviews;

DROP TABLE IF EXISTS IMDB_Movies CASCADE;
DROP TABLE IF EXISTS IMDB_Reviews_Movies CASCADE;
DROP TABLE IF EXISTS IMDB_Reviews_Movies_Predictions CASCADE;
DROP TABLE IF EXISTS IMDB_Series CASCADE;
DROP TABLE IF EXISTS IMDB_Reviews_Series CASCADE;
DROP TABLE IF EXISTS IMDB_Reviews_Series_Predictions CASCADE;

CREATE TABLE IMDB_Movies (
    id_title SERIAL PRIMARY KEY,
    title VARCHAR(255),
    n_reviews INTEGER
);


CREATE TABLE IMDB_Series (
    id_title SERIAL PRIMARY KEY,
    title VARCHAR(255),
    n_reviews INTEGER
);


CREATE TABLE IMDB_Reviews_Movies (
    id SERIAL PRIMARY KEY,
    id_title INTEGER,
    review_rating VARCHAR(10),
    review_title VARCHAR(255),
    review_author VARCHAR(255),
    review_date VARCHAR(50),
    review_text TEXT,
    CONSTRAINT id_title_movie FOREIGN KEY (id_title) REFERENCES IMDB_Movies (id_title)
);


CREATE TABLE IMDB_Reviews_Series (
    id SERIAL PRIMARY KEY,
    id_title INTEGER,
    review_rating VARCHAR(10),
    review_title VARCHAR(255),
    review_author VARCHAR(255),
    review_date VARCHAR(50),
    review_text TEXT,
    CONSTRAINT id_title_series FOREIGN KEY (id_title) REFERENCES IMDB_Series (id_title)
);


CREATE TABLE IMDB_Reviews_Series_Predictions (
    id INTEGER PRIMARY KEY,
    admiration     FLOAT,
    amusement      FLOAT,
    anger          FLOAT,
    annoyance      FLOAT,
    approval       FLOAT,
    caring         FLOAT,
    confusion      FLOAT,
    curiosity      FLOAT,
    desire         FLOAT,
    disappointment FLOAT,
    disapproval    FLOAT,
    disgust        FLOAT,
    embarrassment  FLOAT,
    excitement     FLOAT,
    fear           FLOAT,
    gratitude      FLOAT,
    grief          FLOAT,
    joy            FLOAT,
    love           FLOAT,
    nervousness    FLOAT,
    optimism       FLOAT,
    pride          FLOAT,
    realization    FLOAT,
    relief         FLOAT,
    remorse        FLOAT,
    sadness        FLOAT,
    surprise       FLOAT,
    neutral        FLOAT,
    CONSTRAINT id_review_series FOREIGN KEY (id) REFERENCES IMDB_Reviews_Series (id)
);


CREATE TABLE IMDB_Reviews_Movies_Predictions (
    id INTEGER PRIMARY KEY,
    admiration     FLOAT,
    amusement      FLOAT,
    anger          FLOAT,
    annoyance      FLOAT,
    approval       FLOAT,
    caring         FLOAT,
    confusion      FLOAT,
    curiosity      FLOAT,
    desire         FLOAT,
    disappointment FLOAT,
    disapproval    FLOAT,
    disgust        FLOAT,
    embarrassment  FLOAT,
    excitement     FLOAT,
    fear           FLOAT,
    gratitude      FLOAT,
    grief          FLOAT,
    joy            FLOAT,
    love           FLOAT,
    nervousness    FLOAT,
    optimism       FLOAT,
    pride          FLOAT,
    realization    FLOAT,
    relief         FLOAT,
    remorse        FLOAT,
    sadness        FLOAT,
    surprise       FLOAT,
    neutral        FLOAT,
    CONSTRAINT id_review_movies FOREIGN KEY (id) REFERENCES IMDB_Reviews_Movies (id)
);