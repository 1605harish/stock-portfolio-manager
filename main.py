import mysql.connector
import yfinance as yf
import requests
from datetime import datetime


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





db.commit()


# -------- Helper Functions --------
'''

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


'''
# -------- Main Functions --------





# -------- Interactive User Input Loop --------
'''
while True:
    print("\n--- Enter Transaction Order ---")
    stock = input("Enter stock name (e.g., ETERNAL): ").strip()
    symbol = input("Enter stock symbol (e.g., ETERNAL.NS): ").strip()
    buy_sell = input("Enter order type (BUY/SELL): ").strip().upper()
    qty = int(input("Enter quantity: ").strip())
    #price = float(input("Enter price: ").strip())
    #ticker = yf.Ticker(symbol)


    #df = ticker.history(period='1d', interval='1m')

    price = get_current_price(symbol)
    #print(f"Latest close price (closest to real-time): {price}")


    # Call main order function
    add_order(stock, symbol, buy_sell, qty, price)


    print("Order processed and tables updated.")


    # Optional: Exit condition
    more = input("Do you want to enter another transaction? (yes/no): ").strip().lower()
    if more != "yes":
        break

'''
# Close connections when done
cursor.close()
db.close()
