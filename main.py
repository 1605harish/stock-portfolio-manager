import mysql.connector
import yfinance as yf
import requests
from datetime import datetime
import shutil
cols = shutil.get_terminal_size().columns


# Replace these with your actual DB credentials
DB_HOST = "localhost"
DB_USER = "your_username"
DB_PASS = "your_password"
DB_NAME = "stock_portfolio"


# Connect to MariaDB server (without specifying database first)
db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS
)
cursor = db.cursor()


# Create database if not exists
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
cursor.execute(f"USE {DB_NAME}")


# Create Tables if not exist
# Create tables sequentially
cursor.execute("""
CREATE TABLE IF NOT EXISTS Portfolio (
    stock VARCHAR(50),
    symbol VARCHAR(20) PRIMARY KEY,
    qty INT,
    avg_buy_price FLOAT,
    pl_percent FLOAT,
    user varchar(50)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS OrderBook (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock VARCHAR(50),
    symbol VARCHAR(20),
    buy_sell VARCHAR(4),
    qty INT,
    price FLOAT,
    date_time DATETIME,
    user varchar(50)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ChangePercent (
    stock VARCHAR(50),
    symbol VARCHAR(20) PRIMARY KEY,
    day_1 FLOAT,
    day_5 FLOAT,
    month_1 FLOAT,
    month_6 FLOAT,
    user varchar(50)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Wallet (
    amount INT,
    user varchar(50)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
    user varchar(50),
    password varchar(50)
)
""")
# Commit after all table creations
db.commit()


# -------- Helper Functions --------


def get_current_price(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    return float(data['Close'][0]) if not data.empty else None


def get_change_percent(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="6mo")
    pct = {}
    if not data.empty:
        last = data['Close'].iloc[-1]
        pct['1d'] = ((last - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100 if len(data) > 1 else 0
        pct['5d'] = ((last - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100 if len(data) > 6 else 0
        pct['1m'] = ((last - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100 if len(data) > 21 else 0
        pct['6m'] = ((last - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
    else:
        pct = {'1d': 0, '5d': 0, '1m': 0, '6m': 0}
    return pct

def display_portfolio(username, cursor):
    cursor.execute("SELECT * FROM Portfolio WHERE user = %s", (username,))
    rows = cursor.fetchall()
    if not rows:
        print("Portfolio is empty.")
        return
    print(f"\n{'Stock':<15}{'Symbol':<10}{'Qty':<8}{'Avg Buy Price':<15}{'P/L %':<8}")
    print("-" * cols)
    for row in rows:
        print(f"{row[0]:<15}{row[1]:<10}{row[2]:<8}{row[3]:<15.2f}{row[4]:<8.2f}")

# Dummy placeholder for add_order (implement if you haven't)
def add_order(stock, symbol, buy_sell, qty, price, username, cursor, db):
    # First, fetch current wallet balance for the user
    cursor.execute("SELECT amount FROM Wallet WHERE user=%s", (username,))
    res = cursor.fetchone()
    wallet = res[0] if res else 0

    # Calculate total transaction amount needed
    order_total = price * qty

    if buy_sell.lower() == 'buy':
        if order_total > wallet:
            print("Not enough balance. Order did not get executed.")
            return

        # Check if stock already in portfolio
        cursor.execute("SELECT qty, avg_buy_price FROM Portfolio WHERE symbol=%s AND user=%s", (symbol, username))
        row = cursor.fetchone()
        if row:  # Stock exists, update
            old_qty, old_avg = row
            new_qty = old_qty + qty
            new_avg = ((old_avg * old_qty) + (price * qty)) / new_qty
            # Update avg_buy_price and qty
            cursor.execute("""
                UPDATE Portfolio SET qty=%s, avg_buy_price=%s WHERE symbol=%s AND user=%s
            """, (new_qty, new_avg, symbol, username))
        else:
            # Insert new entry
            cursor.execute("""
                INSERT INTO Portfolio(stock, symbol, qty, avg_buy_price, pl_percent, user)
                VALUES (%s, %s, %s, %s, 0, %s)
            """, (stock, symbol, qty, price, username))

        # Subtract from wallet
        cursor.execute("UPDATE Wallet SET amount=amount-%s WHERE user=%s", (order_total, username))
        db.commit()
        print("Buy order executed and portfolio updated.")

    elif buy_sell.lower() == 'sell':
        # Check quantity in portfolio
        cursor.execute("SELECT qty, avg_buy_price FROM Portfolio WHERE symbol=%s AND user=%s", (symbol, username))
        row = cursor.fetchone()
        if not row:
            print("You do not own this stock. Sell order cancelled.")
            return
        current_qty, avg_buy = row
        if qty > current_qty:
            print("Attempted to sell more than owned. Order cancelled.")
            return
        elif qty == current_qty:
            # Remove from Portfolio
            cursor.execute("DELETE FROM Portfolio WHERE symbol=%s AND user=%s", (symbol, username))
        else:
            # Update qty
            new_qty = current_qty - qty
            cursor.execute("UPDATE Portfolio SET qty=%s WHERE symbol=%s AND user=%s", (new_qty, symbol, username))

        # Add money to wallet
        sale_total = price * qty
        cursor.execute("UPDATE Wallet SET amount=amount+%s WHERE user=%s", (sale_total, username))
        db.commit()
        print("Sell order executed.")

    else:
        print("Invalid order type.")
        return

    # Add order to OrderBook
    now = datetime.now().replace(microsecond=0)
    cursor.execute("""
        INSERT INTO OrderBook(stock, symbol, buy_sell, qty, price, date_time, user)
        VALUES(%s, %s, %s, %s, %s, %s, %s)
    """, (stock, symbol, buy_sell.upper(), qty, price, now, username))
    db.commit()


# -------- Main Functions --------





# -------- Interactive User Input Loop --------

print("Welcome to Zelouda!!\nYour one stop destination to getting financially scammed.")
print("-" * cols)
print("Enter login details")
print("-" * cols)
username = input("Username : ")
password = input("Password : ")

cursor.execute("""
SELECT * FROM Users;
""")

creds = cursor.fetchall()
for i in creds:
    if i[0]==username and i[1]== password:
        print("login successful!! Welcome back",username)



while True:
    print("\nMAIN MENU")
    print("1. Display Portfolio")
    print("2. Enter Transaction Order")
    print("3. Exit")
    choice = input("Enter choice (1/2/3): ").strip()

    if choice == "1":
        display_portfolio(username, cursor)

    elif choice == "2":
        print("\n--- Enter Transaction Order ---")
        stock = input("Enter stock name (e.g., ETERNAL): ").strip()
        symbol = input("Enter stock symbol (e.g., ETERNAL.NS): ").strip()
        buy_sell = input("Enter order type (BUY/SELL): ").strip().upper()
        qty = int(input("Enter quantity: ").strip())
        price = get_current_price(symbol)
        add_order(stock, symbol, buy_sell, qty, price, username, cursor, db)



    elif choice == "3":
        print("Exiting. Goodbye!")
        break
    else:
        print("Invalid choice. Please try again.")



# Close connections when done
cursor.close()
db.close()
