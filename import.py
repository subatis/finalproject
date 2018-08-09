import os
import csv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from models import *

app = Flask(__name__)

# Tell Flask what SQLAlchemy databas to use.
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Link the Flask app with the database (no Flask app is actually being run yet).
db.init_app(app)

def main():
    # Create tables and import from CSV
    db.create_all()

    # Dictionaries to store foreign keys for clues
    category_dict = {}
    round_dict = {}
    value_dict = {}
    air_date_dict = {}

    # Rounds
    with open('data/rounds.csv', encoding="utf8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                round = Round(name=row[0])
                db.session.add(round)
                db.session.flush()
                round_dict[row[0]] = round.id

    # Values
    with open('data/values.csv', encoding="utf8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                value = Value(value=row[0])
                db.session.add(value)
                db.session.flush()
                value_dict[row[0]] = value.id

    # Air dates, show #s
    with open('data/air_dates.csv', encoding="utf8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                air_date = Air_Date(show_num=row[0], air_date=row[1])
                db.session.add(air_date)
                db.session.flush()
                air_date_dict[row[0]] = air_date.id

    # Categories
    with open('data/categories.csv', encoding="utf8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                category = Category(name=row[0], round_id=round_dict[row[1]])
                db.session.add(category)
                db.session.flush()
                category_dict[row[0]] = category.id

    # Clues
    success = 0
    fail = 0
    with open('data/clues.csv', encoding="utf8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                try:
                    clue = Clue(air_date_id=air_date_dict[row[0]], round_id=round_dict[row[2]],
                                category_id=category_dict[row[3]], value_id=value_dict[row[4]],
                                question=row[5], answer=row[6])

                    success += 1
                    print(f"Success: {success}")
                    db.session.add(clue)
                except KeyError:
                    fail += 1
                    print(f"Couldn't match: {fail}")

    # Apply changes
    db.session.commit()

if __name__ == "__main__":
    # Allows for command line interaction with Flask application
    with app.app_context():
        main()
