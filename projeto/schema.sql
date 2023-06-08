CREATE TABLE IMDB_Reviews_Movies (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    review_rating VARCHAR(10),
    review_title VARCHAR(255),
    review_author VARCHAR(255),
    review_date VARCHAR(50),
    review_text TEXT,
    title VARCHAR(255)
);

CREATE TABLE IMDB_Reviews_Series (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    review_rating VARCHAR(10),
    review_title VARCHAR(255),
    review_author VARCHAR(255),
    review_date VARCHAR(50),
    review_text TEXT,
    title VARCHAR(255)
);

CREATE TABLE IMDB_Reviews_Series_Predictions (
    id INTEGER PRIMARY KEY,
    class_1 FLOAT,
    class_2 FLOAT,
    CONSTRAINT id_review_series FOREIGN KEY (id) REFERENCES IMDB_Reviews_Series (id)
);

CREATE TABLE IMDB_Reviews_Movies_Predictions (
    id INTEGER PRIMARY KEY,
    class_1 FLOAT,
    class_2 FLOAT,
    CONSTRAINT id_review_movies FOREIGN KEY (id) REFERENCES IMDB_Reviews_Movies (id)
);