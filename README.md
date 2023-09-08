# Finance-Web-App
This is a solution for CS50's Finance problem set, where you are tasked with creating a web application that allows users to buy and sell stocks. 
This solution is implemented in Python using the Flask web framework and utilizes SQLite for database management.

## How To Run
Clone this repository, navigate to the project and type the following commands:
"1." Activate a virtual environment: 'python3 -m venv .venv' then select the virtual environment as the active workspace
"2." Install dependencies: 'pip install -r requirements.txt'
"3." Run command 'export FLASK_APP=app.py' to set the Flask environment variable
4. [Configure and export your API key with these instructions](https://cs50.harvard.edu/x/2022/psets/9/finance/)
5. Run command 'flask run' to open on localhost
6. When the finance site opens in your browser, register for a new account (upper right corner) to create your own stock portfolio

## Views
### Register
Allow a new user to register for an account, rendering an apology view if the form data is incomplete or if the username already exists in the database.

### Index
The homepage displays a table of the logged-in user's owned stocks, number of shares, current stock price, value of each holding. This view also shows the user's imaginary "cash" balance and the total of their "cash" plus stock value.

### Quote
Allows the user to submit a form to look up a stock's current price, retrieving real-time data from the IEX API. An error message is rendered if the stock symbol is invalid.

### Buy
Allows the user to "buy" stocks by submitting a form with the stock's symbol and number of shares. Checks to ensure the stock symbol is valid and the user can afford the purchase at the stock's current market price with their available balance, and stores the transaction history in the database.

### Sell
Allows the user to "sell" shares of any stock currently owned in their portfolio.

### History
Displays a table summarizing the user's past transactions (all buys and sells). Each row in the table lists whether the stock was bought or sold, the stock's symbol, the buy/sell price, the number of shares, and the transaction's date/time.

Please note that the Login and Logout functions and all functions in helpers.py came with the assignment starter code and are not my work. Starter code ©2020 David J. Malan/ Harvard
