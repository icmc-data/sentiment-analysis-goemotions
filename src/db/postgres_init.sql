CREATE DATABASE imdb_reviews;
\connect imdb_reviews;

DROP TABLE IF EXISTS IMDB_Titles CASCADE;
DROP TABLE IF EXISTS IMDB_Reviews CASCADE;
DROP TABLE IF EXISTS IMDB_Reviews_Predictions CASCADE;

CREATE TABLE IMDB_Titles (
    title_id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    n_reviews INTEGER
);

CREATE TABLE IMDB_Reviews (
    review_id SERIAL PRIMARY KEY,
    title_id INTEGER,
    review_rating VARCHAR(10),
    review_title VARCHAR(255),
    review_author VARCHAR(255),
    review_date VARCHAR(50),
    review_text TEXT,
    CONSTRAINT id_title_movie FOREIGN KEY (title_id) REFERENCES IMDB_Titles (title_id)
);

CREATE TABLE IMDB_Reviews_Predictions (
    review_id INTEGER,
    emotion VARCHAR(20),
    value NUMERIC(12,6),
    PRIMARY KEY (review_id, emotion),
    CONSTRAINT id_review_titles FOREIGN KEY (review_id) REFERENCES IMDB_Reviews (review_id)
);