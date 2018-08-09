import os
from flask import Flask, session, render_template, abort, request
from flask_session import Session
from flask_socketio import SocketIO, emit
from sqlalchemy.sql.expression import func, select
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from models import *
from jeopardy import JeopardyBoard

app = Flask(__name__)

# Configure session to use filesystem and SocketIO
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
Session(app)
socketio = SocketIO(app)

# Set up DB
if not os.getenv("DATABASE_URL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jeopardy.db"
else:
	app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Answer sensitivity (0-100) - defaults to 60 but can change as environmental variable
if not os.getenv("ANSWER_SENSITIVITY"):
	ANSWER_SENSITIVITY = 60
else:
	ANSWER_SENSITIVITY = os.getenv("ANSWER_SENSITIVITY")

# Build game board in session and reset score if new game; by default start fresh "single jeopardy"
def start_game(full_game=False, double_jeopardy=False, reset_score=True):
    session["game_board"] = JeopardyBoard(full_game, double_jeopardy)
    if reset_score or "score" not in session:
    	session["score"] = 0

######################################################################################################################
# Flask Routes             ###########################################################################################
######################################################################################################################

# Home route - random clue generation
@app.route("/")
def index():
	return render_template("index.html", clue=Clue.query.order_by(func.random()).first())

# Game route - show board
@app.route("/game/<string:game_type>")
def game(game_type):
	# Set game type and render
	session["game_type"] = game_type
	return render_template("game.html")

# High scores route
@app.route("/high_scores")
def high_scores():
	return render_template("high_scores.html", scores=High_Score.query.order_by(High_Score.score.desc()))

# About page route
@app.route("/about")
def about():
	return render_template("about.html")

######################################################################################################################
# SocketIO Events          ###########################################################################################
######################################################################################################################

# Once socket is connected, store session ID, set game type and start game
@socketio.on("connected")
def connected():
	session["sid"] = request.sid

	if session["game_type"] == "single":
		start_game()
	elif session["game_type"] == "double":
		start_game(full_game=False, double_jeopardy=True)
	elif session["game_type"] =="full":
		start_game(full_game=True, double_jeopardy=False)
	else:
		abort(404)

	emit("load_board", session["game_board"].categories, room=session["sid"])

# Get specific clue based on id
@socketio.on("get_clue")
def get_clue(data):
	clue = Clue.query.filter_by(id=data["id"]).first()
	emit("show_clue", clue.get_dict(), room=session["sid"])

# Check answer
@socketio.on("check_answer")
def check_answer(data):
	clue = Clue.query.filter_by(id=data["id"]).first()
	if fuzz.partial_ratio(clue.answer, data["input_answer"]) > ANSWER_SENSITIVITY:
		correct = True
		session["score"] += clue.value.value
	else:
		correct = False
		session["score"] -= clue.value.value

	# Update question as answered
	session["game_board"].categories[clue.category.name][clue.value.value]["answered"] = True
	session["game_board"].unanswered_questions-= 1

	emit("answered_question", {'correct': correct, 'score': session["score"], 'correct_answer': clue.answer}, room=session["sid"])

	# If questions remain, reload board
	if session["game_board"].unanswered_questions > 0:
		emit("load_board", session["game_board"].categories, room=session["sid"])
	# If full game and finished single jeopardy, continue game and load double jeopardy
	elif session["game_board"].unanswered_questions == 0 and session["game_board"].full_game and not session["game_board"].double_jeopardy:
		emit("loading_board", room=session["sid"])
		start_game(True, True, False)
		emit("load_board", session["game_board"].categories, room=session["sid"])
	# If full game and double jeopardy completed, load final jeopardy
	elif session["game_board"].unanswered_questions == 0 and session["game_board"].full_game and session["game_board"].double_jeopardy:
		final_jeopardy_id = Round.query.filter_by(name="Final Jeopardy!").first().id
		final_jeopardy_clue = Clue.query.filter_by(round_id=final_jeopardy_id).order_by(func.random()).first()
		emit("show_final_jeopardy_wager", {'category': final_jeopardy_clue.category.name, 'id': final_jeopardy_clue.id,
											'score': session["score"]}, room=session["sid"])
	# Otherwise, tally up score
	else:
		emit("show_final_score", {"score": session["score"], "final_jeopardy": False}, room=session["sid"])

# Get wager for final jeopardy and show clue
@socketio.on("final_jeopardy_wager")
def final_jeopardy_wager(data):
	final_jeopardy_clue = Clue.query.filter_by(id=data["id"]).first()
	session["wager"] = data["wager"]
	emit("show_final_jeopardy_clue", {'clue': final_jeopardy_clue.get_dict(), 'wager': session["wager"]}, room=session["sid"])

# Check final jeopardy answer
@socketio.on("check_final_jeopardy")
def check_final_jeopardy(data):
	final_jeopardy_clue = Clue.query.filter_by(id=data["id"]).first()

	if fuzz.partial_ratio(final_jeopardy_clue.answer, data["input_answer"]) > ANSWER_SENSITIVITY:
		correct = True
		session["score"] += int(session["wager"])
	else:
		correct = False
		session["score"] -= int(session["wager"])

	emit("answered_question", {'correct': correct, 'score': session["score"], 'correct_answer': final_jeopardy_clue.answer}, room=session["sid"])
	emit("show_final_score", {"score": session["score"], "final_jeopardy": True}, room=session["sid"])

# Add a high score
@socketio.on("add_score")
def add_score(data):
	new_score = High_Score(alias=data["alias"], score=session["score"])
	db.session.add(new_score)
	db.session.commit()

	emit("added_score", room=session["sid"])
