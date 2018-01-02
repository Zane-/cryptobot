import logging
from math import floor
from binance.exceptions import BinanceAPIException, BinanceOrderException
from auth import *

logging.basicConfig(level=logging.DEBUG, filename='bot.log')

WATCHING = ['ICXETH', 'TRXETH', 'XLMETH', 'ADAETH', 'IOTAETH', 'XRPETH', 'NAVETH', 'XVGETH']
SELL_VOLUME = 0.3 # percent of volume to sell
RUN_INTERVAL = 120 # in minutes


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


# Returns a tuple containing (lowest, highest) 24hr percent changes among the cryptos in WATCHING.
def get_lowest_highest(data):
    low, high = 0, 0
    for ticker in data:
        change = data[ticker]['change']
        if change > high:
            high, highest = change, ticker
        elif change < low:
            low, lowest = change, ticker
    return (lowest, highest)


# Places a market sell order the crypto. Uses the SELL_VOLUME constant
# to determine the volume to sell.
def sell(ticker):
    b.order_market_sell(
        symbol=ticker,
        quantity=floor(SELL_VOLUME * get_ticker_balance(ticker[0:-3]))) # truncate ETH


# Places a market buy order for the ticker using the specified amount of USD in ether.
def buy(ticker, price, eth):
    vol_ticker = floor(eth / price)
    b.order_market_buy(
        symbol=ticker,
        quantity=floor(vol_ticker * 0.97)) # 97% for fees and price fluctuations


# Places a market buy order for each of the cryptos in WATCHING for the specified amount of USD.
# Used to initially load bot.
def buy_watching(data):
    eth_per = get_ticker_balance('ETH') * 0.97 / len(WATCHING)
    for ticker in data:
        try:
            buy(ticker, data[ticker]['price'], eth_per)
        except (BinanceAPIException, BinanceOrderException) as e:
            print(e)
            logging.exception("Buy order failed:")

def get_vol_watching():
    data = get_watching_data()
    eth_per = get_ticker_balance('ETH') * 0.97 / len(WATCHING)
    return {ticker: eth_per / data[ticker]['price'] for ticker in data}

def run():
    data = get_watching_data()
    lowest, highest = get_lowest_highest(data)
    try:
        sell(highest)
        print('Sold {} for {} at a change of {}'.format(highest, data[highest]['price'], data[highest['change']]))
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Sell order failed:")
        return # do not proceed with buy because ETH balance did not get filled
    try:
        buy(lowest, data[lowest]['price'], get_ticker_balance('ETH'))
        print('Sold {} for {} at a change of {}'.format(lowest, data[lowest]['price'], data[lowest['change']]))
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Buy order failed:")


def main():
    run()


#TODO :
# Add logging of all transactions in an easy-to-get-data-from format
