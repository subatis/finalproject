from sqlalchemy.sql.expression import func, select
from models import *

# Jeopardy game class

class JeopardyBoard:
    # Constructor builds a gameboard based on round (default is "single" jeopardy) - randomly selects categories and clues
    def __init__(self, full_game=False, double_jeopardy=False):
        self.categories = {}
        self.round = Round.query.filter_by(name="Jeopardy!").first()
        self.full_game = full_game
        self.double_jeopardy = double_jeopardy
        self.unanswered_questions = 30
        first_question_value = 200

        # Set to double jeopardy accordingly
        if double_jeopardy:
            self.round = Round.query.filter_by(name="Double Jeopardy!").first()
            first_question_value = 400

        while len(self.categories) < 6:
            # Find a random category in the chosen round that hasn't been chosen already, check to ensure this category has 5 clues
            category = None
            while category is None or category in self.categories:
                category = Category.query.filter_by(round_id=self.round.id).order_by(func.random()).first()

                if Clue.query.filter_by(round_id=self.round.id, category_id=category.id).count() < 5:
                    category = None

            # Get category clues; break out of loop early (e.g < 5 categories) if we can't find all 5 clue values for category
            self.categories[category.name] = {}
            cur_value = first_question_value
            while len(self.categories[category.name]) < 5:
                clue = Clue.query.filter_by(round_id=self.round.id, category_id=category.id,
                                            value_id=Value.query.filter_by(value=cur_value).first().id).first()
                if clue is None:
                    break

                # Create dictionary of clue data
                self.categories[category.name][clue.value.value] = {"id": clue.id, "round": clue.round.name, "category": clue.category.name,
                                                                    "value": clue.value.value, "question": clue.question, "answered": False,
                                                                    "answer": clue.answer, "air_date": clue.air_date.air_date}
                cur_value += first_question_value

            # Ensure we got all 5 clues; if not, delete category and we need to start over
            if len(self.categories[category.name]) < 5:
                del self.categories[category.name]
