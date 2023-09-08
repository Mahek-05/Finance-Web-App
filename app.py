import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    currentPrice = {}
    total = {}
    # To store portfolio of each stock as a list of dictionary in query variable
    query = db.execute("SELECT userid,symbol,name,quantity FROM holdings WHERE userid=?", user_id)

    # To find available cash
    cash = db.execute("SELECT cash FROM users WHERE id=?", user_id)
    grandtotal = cash[0]["cash"]

    # To iterate through each dictionary in the list called query
    for j in query:
        total[j["symbol"]] = lookup(j["symbol"])["price"] * int(j["quantity"])
        currentPrice[j["symbol"]] = lookup(j["symbol"])["price"]
        grandtotal = grandtotal + total[j["symbol"]]

    return render_template("index.html", grandtotal=grandtotal, query=query, cash=cash[0]["cash"], total=total, currentPrice=currentPrice)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        # To find current available cash
        cash_available = db.execute(
            "SELECT cash FROM users WHERE id=?", session["user_id"])

        # Form validation
        # To check if symbol field is blank
        if request.form.get("symbol") == None:
            return apology("Symbol not entered.")
        # To check if shares field is blank
        elif request.form.get("shares") == None:
            return apology("Enter the number of shares.")

        # To check if no. of shares entered is an integer
        try:
            shares_quant = int(request.form.get("shares"))
        except:
            return apology("shares must be an integer.")

        # To check if no. of shares entered is a positive integer
        if shares_quant <= 0:
            return apology("shares must be a positive integer.")
        # To check if symbol is valid or not
        elif lookup(request.form.get("symbol")) == None:
            return apology("Symbol is invalid.")
        # To check if cash available is sufficient or not
        elif float(cash_available[0]["cash"]) < lookup(request.form.get("symbol"))["price"] * shares_quant:
            return apology("Your balance is insufficent.")

        else:
            # To store current date and time
            today = date.today()
            d = today.strftime("%d/%m/%Y")
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")

            # To store info gathered in form
            user_id = session["user_id"]
            symbol = request.form.get("symbol")
            response = lookup(symbol)
            amount = response["price"] * shares_quant
            # Calculate final available cash after buying shares
            new_cash = float(cash_available[0]["cash"] - amount)

            # Record new transaction
            db.execute("INSERT INTO transactions (userid,date,time,symbol,name,price,quantity,total,type) VALUES (?,?,?,?,?,?,?,?,?)",
                       user_id, d, current_time, symbol, response["name"], response["price"], shares_quant, amount, 'bought')
            # Update cash in users table of the current user
            db.execute("UPDATE users SET cash=? WHERE id=? ", new_cash, user_id)
            check = db.execute("SELECT symbol FROM holdings WHERE symbol=? AND userid=?", symbol, user_id)

            # Update holdings table
            if len(check) < 1:
                db.execute("INSERT INTO holdings (userid,symbol,name,quantity) VALUES (?,?,?,?)",
                           user_id, symbol, response["name"], shares_quant)
            else:
                quantity = db.execute("SELECT quantity FROM holdings WHERE userid=? AND symbol=? ",
                                      user_id, symbol)
                db.execute("UPDATE holdings SET quantity=? WHERE symbol=? AND userid=?",
                           int(quantity[0]["quantity"]) + shares_quant, symbol, user_id)

            flash('Purchase Successful')
            return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    # Stores all the transactions in the transactions_history
    transactions_history = db.execute(
        "SELECT * FROM transactions WHERE userid=? ORDER BY id DESC", user_id)
    return render_template("history.html", transactions=transactions_history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted 
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    # Methods = POST
    else:
        symbol = request.form.get("symbol")
        # Checks if symbol is entered or not
        if not symbol:
            return apology("Please enter a symbol")
        # Checks if symbol enterd is valid or not
        elif lookup(symbol) == None:
            return apology("Please enter a valid symbol")
        else:
            item = lookup(symbol)
            stock_name = item["name"]
            stock_symbol = item["symbol"]
            stock_price = item["price"]

            return render_template("quoted.html", stock_name=stock_name, stock_symbol=stock_symbol, stock_price=stock_price)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password1 = request.form.get("password")
        password2 = request.form.get("confirmation")

        special_symbols = ['!', '#', '$', '%', '.', '_', '&']
        # Form validation
        if not username:
            return apology("Username field is empty.")

        if not password1:
            return apology("You must provide a password.")

        if not password2:
            return apology("You must confirm password.")

        if len(password1) < 8:
            return apology("incorrect password format.")

        if not any(char.isdigit() for char in password1):
            return apology("incorrect password format.")

        if not any(char.isupper() for char in password1):
            return apology("incorrect password format.")

        if not any(char in special_symbols for char in password1):
            return apology("incorrect password format.")

        # Checks if password = confrim password
        if password1 == password2:
            password = password1
        else:
            return apology("passwords do not match.")

        pass_hash = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)

        # Checks if username already exists
        if len(db.execute("SELECT username FROM users WHERE username == ?", username)) == 0:
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", username, pass_hash)
            return redirect("/")
        else:
            return apology("This username already exists.")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        query = db.execute(
            "SELECT symbol,quantity FROM holdings WHERE userid=?", session["user_id"])
        return render_template("sell.html", query=query)
    else:
        capital = db.execute(
            "SELECT cash FROM users WHERE id=?", session["user_id"])
        quantity = db.execute("SELECT quantity FROM holdings WHERE userid=? AND symbol=?",
                              session["user_id"], request.form.get("symbol"))

        # Checks if symbol is blank or not
        if request.form.get("symbol") == None:
            return apology("Select a symbol.")

        # Checks if symbol entred is valid or not
        elif lookup(request.form.get("symbol")) == None:
            return apology("Invalid Symbol")

        # Checks if shares is blank or not
        elif request.form.get("shares") == None:
            return apology("Number of shares to be sold not entered")

        # Checks if shares is an integer
        try:
            shares_quant = int(request.form.get("shares"))
        except:
            return apology("shares must be an integer.")

        # Checks if shares is an positive integer
        if shares_quant <= 0:
            return apology("shares must be a positive integer.")
        # Checks if shares available is enough or not
        elif int(request.form.get("shares")) > quantity[0]["quantity"]:
            return apology("Not enough shares")

        else:
            # Stores current date nad time of transaction
            today = date.today()
            d = today.strftime("%d/%m/%Y")
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")

            user_id = session["user_id"]
            symbol = request.form.get("symbol")
            response = lookup(symbol)
            amount = response["price"] * shares_quant
            new_cash = float(capital[0]["cash"] + amount)

            # Records new transaction
            db.execute("INSERT INTO transactions (userid,date,time,symbol,name,price,quantity,total,type) VALUES (?,?,?,?,?,?,?,?,?)",
                       user_id, d, current_time, symbol,  response["name"], response["price"], shares_quant, amount, "Sold")
            # Updates cash vailable for current user in users table
            db.execute("UPDATE users SET cash=? WHERE id=? ",
                       new_cash, user_id)
            # Updates holdings
            db.execute("UPDATE holdings SET quantity=? WHERE userid=? AND symbol=?", int(
                quantity[0]["quantity"]) - shares_quant, user_id, symbol)

            flash('Sold!')
            return redirect("/")
