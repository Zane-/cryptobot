from math import floor
from auth import *


# Returns the total free balance of the ticker in the account.
def fetch_balance(ticker):
    balance_fetched = False
    while not balance_fetched:
        try:
            balance = float(exchange.fetch_balance()[ticker]['free'])
        except ccxt.NetworkError as e:
            continue
        balance_fetched = True
    return balance


# Returns a list of tickers with non-zero balances  in the account.
def fetch_nonzero_balances():
    balances = exchange.fetch_balance()['total']
    return [ticker for ticker in balances if balances[ticker] > 0]


# Returns the price and 24hr change for the ticker.
def fetch_ticker(ticker):
    ticker_fetched = False
    while not ticker_fetched:
        try:
            data = exchange.fetch_ticker(ticker)
        except ccxt.NetworkError as e:
            continue
        ticker_fetched = True
    return {'bid': float(data['bid']), 'change': float(data['change'])}


# Returns a dictionary w/ the prices and percent changes of all cryptos passed in.
def fetch_tickers(tickers):
    return {ticker: fetch_ticker(ticker) for ticker in tickers}


# Places a market sell order for the ticker using the
# given percentage of the available balance.
def sell(ticker, percent):
    sold = False
    while not sold:
        try:
            order = exchange.create_market_sell_order(ticker, floor(fetch_balance(ticker[0:-4]) * (percent/100)))
        except ccxt.ExchangeError as e:
            print(e)
            return None
        except ccxt.NetworkError as e:
            continue
        sold = True
    return order


# Places a limit sell order for the ticker using the
# given percentage of the available balance.
def limit_sell(ticker, percentage, price):
    sell_placed = False
    while not sell_placed:
        try:
            order = exchange.create_limit_sell_order(
                ticker,
                floor(fetch_balance(ticker[0:-4]) * (percentage/100)),
                price)
        except ccxt.ExchangeError as e:
            print(e)
            return None
        except ccxt.NetworkError as e:
            print(e)
            continue
        sell_placed = True
    return order


# Places a market sell order for each of the tickers at the given percentage of
# the total balance.
def sell_tickers(tickers, percent):
    for ticker in data:
        sell(ticker, percent)


# Places a market buy order for the ticker using the specified amount of USD in ether.
# The price of the crypto is given to determine the volume to buy.
def buy(ticker, price, eth):
    amount = floor(eth / price)
    bought = False
    while not bought:
        try:
            order = exchange.create_market_buy_order(ticker, amount)
        except ccxt.InsufficientFunds as e:
            amount *= 0.99 # step down by 1% until order placed
            continue
        except ccxt.NetworkError as e:
            print(e)
            continue
        except ccxt.ExchangeError as e:
            print(e)
            return None
        bought = True
    return order


# Places a limit buy order for the ticker.
def limit_buy(ticker, amount, price):
    buy_placed = False
    while not buy_placed:
        try:
            order = exchange.create_limit_buy_order(
                ticker,
                amount,
                price)
        except ccxt.InsufficientFunds as e:
            amount *= 0.99 # step down by 1% until order placed
            continue
        except ccxt.NetworkError as e:
            print(e)
            continue
        except ccxt.ExchangeError as e:
            print(e)
            return None
        buy_placed = True
    return order


# Places a market buy order for each of the cryptos in the data with
# an equal amount of ether.
def buy_tickers(data):
    eth_per = fetch_balance('ETH')  / len(data.keys())
    for ticker in data:
            buy(ticker, data[ticker]['bid'], eth_per)


# Cancels all open orders for the given ticker.
def cancel_open_orders(ticker):
    for order in exchange.fetch_open_orders(ticker):
        exchange.cancel_order(order['info']['orderId'], ticker)


# Cancels all open orders for the given tickers.
# By default attempts to cancel all nonzero balance coins.
def cancel_all_orders(tickers=None):
    tickers = tickers if tickers is not None else fetch_nonzero_balances()
    tickers.remove('ETH')
    for ticker in tickers:
        cancel_open_orders(ticker)


# Returns the equivalent USD amount of all cryptos in the account.
def get_portfolio():
    eth_usd = fetch_ticker('ETH/USDT')['bid']
    total = eth_usd * fetch_balance('ETH')
    balances = fetch_nonzero_balances()
    balances.remove('ETH')
    for ticker in balances:
        total += eth_usd * fetch_balance(ticker) * fetch_ticker(ticker + '/ETH')['bid']
    return total


# Places a market sell order for the full amount of each of the cryptos in WATCHING.
# Used to redistrubute total funds into all cryptos when distribution becomes too skewed.
def redistribute_funds(data):
    sell_tickers(data.keys())
    buy_tickers(data)
