import logging
from apscheduler.schedules.blocking import BlockingScheduler
from binance.exceptions import BinanceAPIException, BinanceOrderException
from auth import *

logging.basicConfig(level=logging.DEBUG, filename='bot.log')

WATCHING = ['ICXETH', 'TRXETH', 'XLMETH', 'ADAETH', 'IOTAETH', 'XRPETH', 'NAVETH', 'XVGETH']
SELL_VOLUME = 0.3 # percent of volume to sell
RUN_INTERVAL = 120 # in minutes

# Returns a dictionary w/ the prices and percent changes of all cryptos in the WATCHING list
def get_watching_data():
    prices = {}
    for ticker in WATCHING:
        data = b.get_ticker(symbol=ticker)
        prices[ticker] = {}
        prices[ticker]['price'] = float(data['lastPrice'])
        prices[ticker]['change'] = float(data['priceChangePercent'])
    return prices


high = lambda x, y: x > y # compare functions for get_greatest_change
low = lambda x, y: x < y
# Returns a list containing the ticker with the highest change (high or low),
# the change, and the last price.
def get_greatest_change(comp=high):
    data = get_watching_data()
    greatest = [0, 0, 0] # [ticker, 24hr change, price]
    for ticker in data:
        change = data[ticker]['change']
        if comp(change, greatest[1]):
            greatest[0] = ticker
            greatest[1] = change
            greatest[2] = data[ticker]['price']
    return greatest


# Places a market sell order for the crypto with the highest 24hr increase.
def sell_highest():
    highest = get_greatest_change()
    b.order_market_sell(
        symbol=highest[0],
        quantity=SELL_VOLUME * b.get_asset_balance(asset=greatest[0][0:-3]) # truncate ETH)


# Places a market buy order for the crypto with the highest 24hr decrease.
def buy_lowest():
    lowest = get_greatest_change(comp=low)
    b.order_market_buy(
       symbol=lowest[0],
       # buy with 97% ETH balance because we sell highest into ETH first
       # and we don't want rounding errors to not let the order go through
       quantity=b.get_asset_balance(asset='ETH') * 0.97 / lowest['price'])

def run():
    try:
        sell_highest()
    except (BinanceAPIException, BinanceOrderException):
        logging.exception("Sell Order Failed:")
        exit()

    try:
        buy_lowest()
    except (BinanceAPIException, BinanceOrderException):
        logging.exception("Buy Order Failed:")


def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(run, 'interal', minutes=RUN_INTERVAL)
    scheduler.start()
