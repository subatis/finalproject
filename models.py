from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Which round of Jeopardy - Single, Double, Final
class Round(db.Model):
    __tablename__ = "rounds"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return self.name

# Value of clue (0 = Final Jeopardy)
class Value(db.Model):
    __tablename__ = "values"
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, unique=True, nullable=False)

    def __repr__(self):
        return str(self.value)

# A Jeopardy category (all unique)
class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=False, nullable=False)

    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'), nullable=False)
    round = db.relationship("Round", backref="categories", lazy=True)

    def __repr__(self):
        return self.name

# Air date/number of Jeopardy episode
class Air_Date(db.Model):
    __tablename__ = "air_dates"
    id = db.Column(db.Integer, primary_key=True)
    show_num = db.Column(db.Integer, unique=True, nullable=False)
    air_date = db.Column(db.String(12), unique=True, nullable=False)

    def __repr__(self):
        return self.air_date

# Jeopardy clue - incorporates all of the above
class Clue(db.Model):
    __tablename__ = "clues"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, unique=True, nullable=False)
    answer = db.Column(db.Text, unique=False, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category = db.relationship("Category", backref="clues", lazy=True)

    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'), nullable=False)
    round = db.relationship("Round", backref="clues", lazy=True)

    value_id = db.Column(db.Integer, db.ForeignKey('values.id'), nullable=False)
    value = db.relationship("Value", backref="clues", lazy=True)

    air_date_id = db.Column(db.Integer, db.ForeignKey('air_dates.id'), nullable=False)
    air_date = db.relationship("Air_Date", backref="clues", lazy=True)

    def get_dict(self):
        return {'id': self.id, 'category': self.category.name, 'value': self.value.value, 'question': self.question, 'answer': self.answer}

    def __repr__(self):
        return str(self.id)

# High scores table
class High_Score(db.Model):
    __tablename__ = "high_scores"
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(40), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return str(self.score)

