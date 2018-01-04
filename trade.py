import csv
import logging
from collections import deque
from datetime import datetime
from math import floor

from binance.exceptions import BinanceAPIException, BinanceOrderException
from auth import *

logging.basicConfig(level=logging.DEBUG, filename='bot.log')

WATCHING = ['ICXETH', 'TRXETH', 'XLMETH', 'ADAETH', 'IOTAETH', 'XRPETH', 'NAVETH', 'XVGETH']
SELL_VOLUME = 0.3 # percent of volume to sell in the run function


# Returns the total free balance of the ticker in the account.
def get_ticker_balance(ticker):
    return float(b.get_asset_balance(asset=ticker)['free'])


# Returns the price and 24hr change for the ticker.
def get_ticker_data(ticker):
    data = b.get_ticker(symbol=ticker)
    return {'price': float(data['lastPrice']), 'change': float(data['priceChangePercent'])}


# Returns a dictionary w/ the prices and percent changes of all cryptos in WATCHING.
def get_watching_data():
    return {ticker: get_ticker_data(ticker) for ticker in WATCHING}


# Returns a tuple containing (lowest, highest) 24hr percent changes
# among the cryptos in WATCHING.
def get_lowest_highest(data):
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
    b.order_market_sell(
        symbol=ticker,
        quantity=floor(percent * get_ticker_balance(ticker[0:-3]))) # truncate ETH


# Places a market buy order for the ticker using the specified amount of USD in ether.
# The price of the crypto is given to determine the volume to buy.
def buy(ticker, price, eth):
    vol_ticker = floor(eth / price)
    b.order_market_buy(
        symbol=ticker,
        quantity=floor(vol_ticker * 0.97)) # 97% for fees and price fluctuations


# Places a market buy order for each of the cryptos in WATCHING
# for the specified amount of USD. Used to initially load bot.
def buy_watching(data):
    eth_per = get_ticker_balance('ETH') * 0.97 / len(WATCHING)
    for ticker in data:
        try:
            buy(ticker, data[ticker]['price'], eth_per)
        except (BinanceAPIException, BinanceOrderException) as e:
            print(e)
            logging.exception("Buy order failed:")


# Places a market sell order for the full amount of each of the cryptos in WATCHING.
# Used to redistrubute total funds into all cryptos when distribution becomes too skewed.
def redistribute_funds(data):
    for ticker in data:
        try:
            sell(ticker, 1.0)
        except (BinanceAPIException, BinanceOrderException) as e:
            print(e)
            logging.exception("Redistribution failed:")
    # error catching done in buy_watching()
    buy_watching(data)


# Returns the equivalent USD amount of all cryptos in the account.
def get_portfolio(data):
    eth_usd = get_ticker_data('ETHUSDT')['price']
    total = eth_usd * get_ticker_balance('ETH')
    for ticker in data:
        total += eth_usd * get_ticker_balance(ticker[0:-3]) * data[ticker]['price']
    return total


# Returns the portfolio percent change from the last transaction using the transactions csv.
def get_portfolio_change(data):
    last_portfolio = float(get_last_row('transactions.csv')[9])
    return round(get_portfolio(data) / last_portfolio, 4)


# Returns the last row of the filename
def get_last_row(filename):
    with open(filename) as f:
        return deque(csv.reader(f), 1)[0]

#generalizes the trading strategy
def initial_trading_strategy(num):
    data = get_watching_data()
    eth_per = get_ticker_balance('ETH') / num * 0.98
    for x in range(0, num):
        lowest, highest = get_lowest_highest(data)
        data.pop(lowest, None)
        data.pop(highest, None)

        try:
            sell(highest, SELL_VOLUME)
        except (BinanceAPIException, BinanceOrderException) as e:
            print(e)
            logging.exception("Sell order failed:")
            return # do not proceed with buy because ETH balance did not get filled

        try:
            buy(lowest, data[lowest]['price'], eth_per)
        except (BinanceAPIException, BinanceOrderException) as e:
            print(e)
            logging.exception("Buy order failed:")

# Sells the two highest percent change cryptos and the buys the two lowest.
def main():
    initial_trading_strategy(2)

    # write data to CSV
    row = (
        str(datetime.now()),
        lowest,
        data[lowest]['change'],
        second_lowest,
        data[second_lowest]['change'],
        second_highest,
        data[second_highest]['change'],
        highest,
        data[highest]['change'],
        round(get_portfolio(data), 2),
        get_portfolio_change(data)
    )

    with open('transactions.csv', 'a') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(row)


if __name__ == '__main__':
    main()