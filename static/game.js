// Handlebars templates
const SQUARE_TEMPLATE = Handlebars.compile(document.querySelector('#template-jeopardy-square').innerHTML);
const QUESTION_TEMPLATE = Handlebars.compile(document.querySelector('#template-jeopardy-clue-view').innerHTML);
const FINAL_JEOPARDY_WAGER_TEMPLATE = Handlebars.compile(document.querySelector('#template-final-jeopardy-wager').innerHTML);
const FINAL_JEOPARDY_CLUE_TEMPLATE = Handlebars.compile(document.querySelector('#template-final-jeopardy-clue').innerHTML);

// On DOM load
document.addEventListener('DOMContentLoaded', () => {
    // Connect to socket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // On connect, start game and load board (see below)
    socket.on('connect', () => {
        socket.emit('connected');
    });

    // Load board
    socket.on('load_board', data => {
        var boardHTML = '<div class="row no-gutters board-categories">';

        // Build category headers
        var categoryNames = Object.keys(data);
        for (let i = 0; i < categoryNames.length; ++i) {
            const category = SQUARE_TEMPLATE({'text': categoryNames[i]});
            boardHTML += category;
        }

        boardHTML += '</div>';

        // Build category columns
        var boardClues = [];
        Object.keys(data).forEach(function(key, index) {
            Object.keys(this[key]).forEach(function(key, index) {
                var cell ='';

                if (!this[key].answered) {
                    cell = SQUARE_TEMPLATE({'answered_or_unanswered': 'game-clue-unanswered', 'id': this[key].id, 'text': '$' + this[key].value});
                }
                else {
                    cell = SQUARE_TEMPLATE({'answered_or_unanswered': 'game-clue-answered'});
                }

                boardClues.push(cell);
            }, this[key]);
        }, data);

        // Add columns to board
        for (var i = 0; i < 5; ++i) {
            boardHTML += '<div class="row no-gutters board-clues">';

            // The similar-valued clues are 5 indices apart
            for (var j = i; j < 30; j += 5) {
                boardHTML += boardClues[j];
            }

            boardHTML += '</div>';
        }

        // Show board
        document.querySelector('#game-board').innerHTML = boardHTML;

        // Create button click functionality to show clues
        document.querySelectorAll('.game-clue-unanswered').forEach(function(clue) {
            clue.onclick = function() {
                socket.emit('get_clue', {'id': this.id});
                return false;
            };
        });
    });

    // Show board loading between rounds while board is prepared on the server
    socket.on('loading_board', () => {
        document.querySelector('#game-board').innerHTML = 'Loading board...';
    });

    // Show clue and assign answer functionality to button
    socket.on('show_clue', data => {
        const question = QUESTION_TEMPLATE({'question': data.question, 'category': data.category, 'value': data.value});
        document.querySelector('#game-board').innerHTML = question;
        document.querySelector('#btn-answer-submit').onclick = () => {
            socket.emit('check_answer', {'id': data.id, 'input_answer': document.querySelector('#txt-answer-input').value});
            return false;
        };
    });

    // Answered question - alert user and update displayed score
    socket.on('answered_question', data => {
        var scoreHTML = '<b>';
        if (data.score < 0) {
            scoreHTML += '<font color="red">-$' + Math.abs(data.score);
        }
        else {
            scoreHTML += '<font>$' + data.score;
        }
        scoreHTML += '</b></font>';

        document.querySelector('#player-score').innerHTML = scoreHTML;

        if (data.correct) {
            correct = 'Correct!';
        }
        else {
            correct = 'Sorry, that\'s not correct.';
        }

        document.querySelector('#player-score').innerHTML += '<br>' + correct;
        document.querySelector('#player-score').innerHTML += '<br>The answer was: ' + data.correct_answer;
    });

    // Show final score, and prompt for alias name if a full game is played (for high scores list)
    socket.on('show_final_score', data => {
        scoreHTML = '<div class="row"><div class="col-12 text-center final-score"><h2>Final score: ';

        if (data.score < 0) {
            scoreHTML += '<font color="red">-$' + Math.abs(data.score);
        }
        else {
            scoreHTML += '<font>$' + data.score;
        }
        scoreHTML += '</b></font>';
        scoreHTML += '</div></div>';

        if (data.final_jeopardy) {
            scoreHTML += '<div class="row"><div class="col-12"><form class="form-inline justify-content-center">';
            scoreHTML += '<input type="text" class="form-control mb-2 mr-sm-2 mb-sm-0" id="txt-alias-input" placeholder="Type alias"></input>';
            scoreHTML += '<button type="submit" class="btn btn-primary" id="btn-alias-submit">Submit</button></form>';
            scoreHTML += '</div></div>';
        }

        document.querySelector('#game-board').innerHTML = scoreHTML;

        if (data.final_jeopardy) {
            document.querySelector('#btn-alias-submit').onclick = () => {
                alias = document.querySelector('#txt-alias-input').value;

                if (alias.trim().length === 0) {
                    alert('Please enter a valid alias (cannot be blank).');
                }
                else {
                    socket.emit('add_score', {'alias': alias});
                }

                return false;
            };
        }
    });

    // Show final jeopardy WAGER and add functionality to submit button
    socket.on('show_final_jeopardy_wager', data => {
       finalJepHTML = FINAL_JEOPARDY_WAGER_TEMPLATE({'category': data.category});
       document.querySelector('#game-board').innerHTML = finalJepHTML;

       document.querySelector('#btn-wager-submit').onclick = () => {
            var wager = document.querySelector('#txt-wager-input').value;

            if (data.score <= 0) {
                alert('You don\'t have enough money to wager anything--setting wager to zero.');
                socket.emit('final_jeopardy_wager', {'id': data.id, 'wager': 0});
            }
            else if (wager > data.score) {
                alert('You don\'t have enough money to make that wager!');
            }
            else if (wager.trim().length === 0 || isNaN(wager)) {
                alert('Your input was invalid. Please type a number!');
            }
            else {
                socket.emit('final_jeopardy_wager', {'id': data.id, 'wager': wager});
            }

            return false;
        };
    });

    // Show final jeopardy CLUE and add functionality to submit button
    socket.on('show_final_jeopardy_clue', data => {
       finalJepHTML = FINAL_JEOPARDY_CLUE_TEMPLATE({'category': data.clue.category, 'wager': data.wager, 'question': data.clue.question});
       document.querySelector('#game-board').innerHTML = finalJepHTML;

       document.querySelector('#btn-answer-submit').onclick = () => {
            socket.emit('check_final_jeopardy', {'id': data.clue.id, 'input_answer': document.querySelector('#txt-answer-input').value});
            return false;
        };
    });

    // After adding high score
    socket.on('added_score', () => {
        document.querySelector('#game-board').innerHTML = '<div class="row"><div class="col-12" id="thanks-for-playing"><h1>Thanks for playing!</h1></div></div>';
    });

});
