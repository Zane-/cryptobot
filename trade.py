import logging
from apscheduler.schedulers.blocking import BlockingScheduler
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
    greatest = {}
    for ticker in data:
        change = data[ticker]['change']
        if comp(change, greatest[1]):
            greatest['ticker'] = ticker
            greatest['change'] = change
            greatest['price'] = data[ticker]['price']
    return greatest


# Places a market sell order for the crypto with the highest 24hr increase.
def sell_highest():
    highest = get_greatest_change()
    b.order_market_sell(
        symbol=highest['ticker'],
        quantity=SELL_VOLUME * b.get_asset_balance(asset=greatest['ticker'][0:-3])) # truncate ETH


# Places a market buy order for the crypto with the highest 24hr decrease.
def buy_lowest():
    lowest = get_greatest_change(comp=low)
    b.order_market_buy(
       symbol=lowest['ticker'],
       # buy with 97% ETH balance because we sell highest into ETH first
       # and we don't want rounding errors to not let the order go through
       quantity=b.get_asset_balance(asset='ETH') * 0.97 / lowest['price'])


# Places a market buy order for the ticker using the specified amount of USD in ether.
def buy(ticker, usd):
    eth_usd = b.get_ticker(symbol='ETHUSDT')['lastPrice'] # 760
    eth_bal = b.get_asset_balance(asset='ETH')
    if (eth_bal * eth_usd) < (usd * 0.97):
        raise BinanceOrderException
    vol_eth = eth_usd * usd
    vol_ticker = vol_eth / b.get_ticker(symbol=ticker)['lastPrice']
    try:
        b.order_market_buy(
            symbol=ticker,
            quantity=vol_ticker * 0.97) # 97% for fees and price fluctuations
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Buy order failed:")


# Places a market buy order for each of the cryptos in WATCHING for the specified amount of USD.
def buy_watching(usd):
    for ticker in WATCHING:
        try:
            buy(ticker, usd)
        except BinanceOrderException as e:
            print(e)
            logging.exception("Buy order failed:")


def run():
    try:
        sell_highest()
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Sell order failed:")
        return
    try:
        buy_lowest()
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Buy order failed:")


def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(run, 'interval', minutes=RUN_INTERVAL)
    scheduler.start()
