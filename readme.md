First, thanks for all your help througout the course Alex. As per my status update, wrangling the data and putting together the
game logic proved to be much more difficult and time consuming than originally anticipated, so I had to adjust the scope from my
original starry-eyed vision--but I am pretty happy with how the app came out overall.

General notes:

-There are 4 pages:
-->Homepage displays a random clue with each refresh
-->High scores displays a list of scores & aliases. It's pretty tough to just break even when you are forced to enter answers for ALL
    clues, so any player who completes a full game is prompted to enter their score.
-->GAME route allows a play to play: a "regular" jeopardy round, a "double" jeopardy round, or a FULL game, which includes final jeopardy
-->About page that just contains links/references

-The game makes heavy use of SESSIONS to support multiple users playing at once. The game itself utilizes SocketIO to play it
asynchronously w/o refresh. However, a game in-progress REFRESHES altogether if the page is closed or refreshed.
-->I would've liked to restore a game that is currently in-play, however I ran out of time to support & test this adequately.

-When going from "regular" Jeopardy round to "double" Jeopardy in a full game, note that the board needs to load and it will take a
second (more on this below). I tried to have the app show "loading board..." again (you will see it in the code), however, for whatever
reason this doesn't fire, and I couldn't figure out why. Not a huge deal, but 1) feedback is appreciated and 2) just give it 2 seconds
if you get to this part to let the board load (it will)

-The app utilizes a SQLite database to hold the ~200,000 available Jeopardy clues. I would've loved to host this up on Heroku using
PostgreSQL instead, but the cap of 10,000 or so records made that impossible, so I opted to use SQLite so as not to spend money

-The SQLITE DB is called jeopardy.db -- DATABASE_URL should be set to sqlite:///jeopardy.db
-->Note that application.py checks for the environment's DATABASE_URL and if it isn't found, it defaults to the above...
    is that bad practice? why?

-The app uses a Python package called FuzzyWuzzy for answer checking. This package is an extension of DiffLib in Python to do fuzzy
string matching. I listed it in requirements, but just an FYI that it needs to be installed
-->The string matching returns a ratio value from 0-100 and mostly assesses substrings(I used partial_ratio instead of just ratio,
since the clue answer data was all over the place). It is far from perfect but appears accurate 90+% of the time or so.
-->The reason it misses at times is because the answer data is messy. There are typos; sometimes it will include things like
"(also acceptable: answer2)"; sometimes it only includes a person's last name vs. sometimes full names and in reality Jeopardy should
accept both; among many other reasons. Like I said though, I think it works pretty well, considering.
-->You can change the ANSWER_SENSITIVITY via environment variable with that name, but it defaults to 60, which appears to work pretty well

-I spent a good amount of time cleaning/splitting the data, and writing an import routine to bring it into the SQLite DB the steps were:
1) parsed out CSV file into separate files
    -->air date(includes show number)
    -->category
    -->value
    -->round
    -->clue, which brings all of this together

2) wrangled with the data by deduping and other cleanup in Excel, and/or skipping some values via python code

3) attempted to import this into SQLite tables via import.py and SQLAlchemy

4) repeated steps 2 and 3 all day long until finally successful

5) end result: roughly 205,000 out of 215,000 clues imported (~95%)

6) I added the high scores table manually later using a SQLite viewer

-Some of the clues have URLs in them. I let jinja/handlebars escape the usual HTML stripping so these would be shown as actual links
-->This is often a GOOD thing, as many of the links work! A pleasant side effect of the big, messy data set
-->However, at the same time, some links are broken, which is too bad

-Special characters (like in "El Nino") did not carry over into the DB well, but I only enountered this once or twice

-All in all, DATA CLEANUP would be an important aspect of making this "production-ready"

-Most logic is in the GAME portion of the app (e.g. for building and playing through Jeopardy)
-->Because of the messy data, it was not guaranteed that a given category has 5 clues for a full board, and/or that it had the
appropriately valued clues (typos). Thus the board-building logic would:
    1) Select a category randomly
    2) Perform a quick check to ensure this category has at least 5 clues
    3) Match clues with needed values (200/400/600/800/1000 or 400/800/1200/1600/2000 for regular/double jeopardy respectively)
    4) If no match, go back to step 1; otherwise add category
    5) Once completed, return the board as an object. The "categories" dictionary (a nested dictionary, really) is what gets passed
        to the templates/pages for rendering.
-->This worked very well but the board can take a couple seconds to load

Files:
jeopardy.db - The DB. I split up most of the data into separate tables so that clues would relate on foreign keys.
import.py - The import routine I used to bring in the bulk of the data. It counts successes/failures as records are imported
/data/ - this folder contains the individual broken up CSV files used for import.py. the subfolder is the original raw data
models.py - The SQLAlchemy models that represent what is in the DB; these are pretty self-explanatory
jeopardy.py - class that represents a Jeopardy game board. All logic is in the constructor. see above for more explanation
application.py - the core of the app, mostly contains the flask routes and socketIO events
game.js - the logic associated with game.html; allows a full game of jeopardy to be played w/o refreshing using SocketIO
game.html - game page, see game.js above
layout.html - base template that contains the header and loads core CSS/Bootstrap stuff among other things
index.html - homepage that displays random clue using Jinja
high_scores.html - scores page that displays list of scores using Jinja
about.html - about page with simple info about how app was built, where data came from
logo.png - Jeopardy! logo (only image) -- for header/banner
styles.css - styling. I opted not to use SCSS here since I am too terrible at CSS to bother with the recompiling, etc.

Project reqs:
Project must utilize 2 of 3 Python/JavaScript/SQL:
    -->Project uses all 3 extensively:
        -->Python - Flask (& Jinja), SQLALchemy, SocketIO
        -->JavaScript SocketIO/general asynchronous update functionality, Handlebars
        -->SQL - SQLite

Mobile-responsive:
    -->The app works pretty well on Mobile (tested on my phone & using Chrome's simulation).
    -->Didn't need to use breakpoints since the app was simply enough
    -->In that sense, I relied on 2 things mostly:
        -->BOOTSTRAP of course!
        -->The "vw" sizing for fonts, which sizes them based on viewport; this allows the app to adjust font size on the fly
            with the viewport. It appears vw isn't supported in older browsers, but considering this course really only focused
            on the latest versions of stuff, I figured legacy support wasn't a huge issue

SOURCES

Getting random row via SQLAlchemy/SQLite-
https://stackoverflow.com/questions/60805/getting-random-row-through-sqlalchemy
https://stackoverflow.com/questions/1253561/sqlite-order-by-rand <-- using random() in SQLite instead of rand()

looping over dictionaries in javascript-
https://stackoverflow.com/questions/18804592/javascript-foreach-loop-on-associative-array-object

fuzzy string comparison - e.g. where i found fuzzywuzzy
https://stackoverflow.com/questions/10383044/fuzzy-string-comparison

use triple brackets to avoid escaping HTML in handlebars templates (for clues that include HTML)
https://stackoverflow.com/questions/20280601/insert-html-in-a-handlebar-template-without-escaping

navbar colors in bootstrap
https://stackoverflow.com/questions/18529274/change-navbar-color-in-twitter-bootstrap

what fonts for jeopardy?
https://www.quora.com/What-font-is-used-for-Jeopardy-categories

pass HTML to jinja 2 by declaring it safe
https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2

bootstrap - navbar height
https://stackoverflow.com/questions/43107757/how-do-you-decrease-navbar-height-in-bootstrap-4

check whether input is a number-
https://stackoverflow.com/questions/18042133/check-if-input-is-number-or-letter-javascript
