import csv
from collections import deque
from datetime import datetime
from math import floor

from auth import *


WATCHING = ['ICX/ETH', 'TRX/ETH', 'XLM/ETH', 'ADA/ETH', 'IOTA/ETH', 'XRP/ETH', 'NAV/ETH', 'XVG/ETH']
SELL_VOLUME = 30 # percent of volume to sell in the run function


# Returns the total free balance of the ticker in the account.
def fetch_balance(ticker):
    balance_fetched = False
    while not balance_fetched:
        try:
            balance = float(binance.fetch_balance()[ticker]['free'])
        except ccxt.NetworkError as e:
            continue
        balance_fetched = True
    return balance


# Returns the price and 24hr change for the ticker.
def fetch_ticker(ticker):
    ticker_fetched = False
    while not ticker_fetched:
        try:
            data = binance.fetch_ticker(ticker)
        except ccxt.NetworkError as e:
            continue
        ticker_fetched = True
    return {'bid': float(data['bid']), 'change': float(data['change'])}


# Returns a dictionary w/ the prices and percent changes of all cryptos passed in.
def fetch_tickers(tickers):
    return {ticker: fetch_ticker(ticker) for ticker in tickers}


# Returns a tuple containing (lowest, highest) 24hr percent changes
# among the cryptos in WATCHING.
def fetch_lowest_highest(data):
    low, high = 0, 0
    for ticker in data:
        change = data[ticker]['change']
        if change > high:
            high, highest = change, ticker
        elif change < low:
            low, lowest = change, ticker
    return (lowest, highest)


# Places a market sell order for the ticker using the
# given percentage of the available balance.
def sell(ticker, percent):
    sold = False
    while not sold:
        try:
            order = binance.create_market_sell_order(ticker, floor(fetch_balance(ticker[0:-4]) * (percent/100)))
        except ccxt.ExchangeError as e:
            print(e)
            return None
        except ccxt.NetworkError as e:
            continue
        sold = True
    return order


# Places a market buy order for the ticker using the specified amount of USD in ether.
# The price of the crypto is given to determine the volume to buy.
def buy(ticker, price, eth):
    vol_ticker = floor(eth / price)
    bought = False
    while not bought:
        try:
            order = binance.create_market_buy_order(ticker, vol_ticker * 0.98) # 98% for fees and fluctuations
        except ccxt.InsufficientFunds as e:
            price = price * 1.01
            continue
        except ccxt.NetworkError as e:
            continue
        except ccxt.BaseError as e:
            print(e)
            return None
        bought = True
    return order


# Places a market buy order for each of the cryptos in WATCHING
# for the specified amount of USD. Used to initially load bot.
def buy_tickers(data):
    eth_per = fetch_balance('ETH')  / len(data.keys())
    for ticker in data:
            buy(ticker, data[ticker]['bid'], eth_per)


# Places a market sell order for the full amount of each of the cryptos in WATCHING.
# Used to redistrubute total funds into all cryptos when distribution becomes too skewed.
def redistribute_funds(data):
    for ticker in data:
        sell(ticker, 1.0)
    buy_tickers(data)


# Returns the equivalent USD amount of all cryptos in the account.
def get_portfolio(data):
    eth_usd = fetch_ticker('ETH/USDT')['bid']
    total = eth_usd * fetch_balance('ETH')
    for ticker in data:
        total += eth_usd * fetch_balance(ticker[0:-4]) * data[ticker]['bid']
    return total


# Returns the portfolio percent change from the last transaction using the transactions csv.
def get_portfolio_change(data):
    last_portfolio = float(get_last_row('transactions.csv')[9])
    return round(get_portfolio(data) / last_portfolio, 4)


# Returns the last row of the filename
def get_last_row(filename):
    with open(filename) as f:
        return deque(csv.reader(f), 1)[0]


# Sells the num highest percent change cryptos and the buys the num lowest.
def low_high_pair_strat(num, watching=WATCHING):
    data = fetch_tickers(watching)
    eth_per = fetch_balance('ETH') / num * 0.98
    for _ in range(num):
        lowest, highest = get_lowest_highest(data)
        data.pop(lowest, None)
        data.pop(highest, None)
        try:
            sell(highest, SELL_VOLUME)
        except ccxt.ExchangeError as e:
            print(e)
            return # do not proceed with buy
        buy(lowest, data[lowest]['bid'], eth_per)


def main():
    low_high_pair_strat(2)

    # TODO:
    # * dropbox integration here w/ csv

    # write data to CSV
    # row = (
    #     str(datetime.now()),
    #     lowest,
    #     data[lowest]['change'],
    #     second_lowest,
    #     data[second_lowest]['change'],
    #     second_highest,
    #     data[second_highest]['change'],
    #     highest,
    #     data[highest]['change'],
    #     round(get_portfolio(data), 2),
    #     get_portfolio_change(data)
    # )

    # with open('transactions.csv', 'a') as f:
    #     writer = csv.writer(f, lineterminator='\n')
    #     writer.writerow(row)


if __name__ == '__main__':
    main()
