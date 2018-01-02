import logging
from math import floor
from binance.exceptions import BinanceAPIException, BinanceOrderException
from auth import *

logging.basicConfig(level=logging.DEBUG, filename='bot.log')

WATCHING = ['ICXETH', 'TRXETH', 'XLMETH', 'ADAETH', 'IOTAETH', 'XRPETH', 'NAVETH', 'XVGETH']
SELL_VOLUME = 0.3 # percent of volume to sell


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
def sell(ticker, percent):
    b.order_market_sell(
        symbol=ticker,
        quantity=floor(percent * get_ticker_balance(ticker[0:-3]))) # truncate ETH


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

#Places a market sell order for the full amount of each of the cryptos in WATCHING
#Used to redistrubute total funds into all cryptos when distribution becomes too skewed
def redistribute_funds(data):
    for ticker in data:
        try:
            sell(ticker, 1.0)
        except (BinanceAPIException, BinanceOrderException) as e:
            print(e)
            logging.exception("Redistribution failed:")
    #error catching done in buy_watching()
    buy_watching(data)


def run():
    data = get_watching_data()
    lowest, highest = get_lowest_highest(data)
    lowest_data = data.pop(lowest, None)
    highest_data = data.pop(highest, None)
    second_lowest, second_highest = get_lowest_highest(data)
    try:
        sell(highest, SELL_VOLUME)
        print('Sold {} for {} at a change of {}'.format(highest, highest_data['price'], highest_data['change']))
        sell(second_highest, SELL_VOLUME)
        print('Sold {} for {} at a change of {}'.format(second_highest, data[second_highest]['price'], data[second_highest]['change']))
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Sell order failed:")
        return # do not proceed with buy because ETH balance did not get filled
    try:
        eth_per = get_ticker_balance('ETH') / 2 * 0.98
        buy(lowest, lowest_data['price'], eth_per)
        print('Bought {} for {} at a change of {}'.format(lowest, lowest_data['price'], lowest_data['change']))
        buy(lowest, data[second_lowest]['price'], eth_per)
        print('Bought {} for {} at a change of {}'.format(lowest, data[second_lowest]['price'], data[second_lowest]['change']))
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Buy order failed:")


if __name__ == '__main__':
    run()

# TODO :
# Add logging of all transactions in an easy-to-get-data-from format (csv)
# Add checks to not trade if the