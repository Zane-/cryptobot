import logging
from apscheduler.schedulers.blocking import BlockingScheduler
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
    low, high = 0
    for ticker in data:
        change = data[ticker]['change']
        if change > high:
            high = change
            highest = ticker
        elif change < low:
            low = change
            lowest = ticker
    return (lowest, highest)


# Places a market sell order the crypto. Uses the SELL_VOLUME constant
# to determine the volume to sell.
def sell(ticker):
    b.order_market_sell(
        symbol=ticker,
        quantity=SELL_VOLUME * get_ticker_balance(ticker[0:-3]))


# Places a market buy order for the ticker using the specified amount of USD in ether.
def buy(ticker, price, eth):
    vol_ticker = eth / price
    try:
        b.order_market_buy(
            symbol=ticker,
            quantity=vol_ticker * 0.97) # 97% for fees and price fluctuations
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Buy order failed:")


# Places a market buy order for each of the cryptos in WATCHING for the specified amount of USD.
def buy_watching(data):
    eth_per = get_ticker_balance('ETH') * 0.97 / len(watching)
    for ticker in data:
        buy(ticker, ticker['price'], eth_per)


def run():
    data = get_watching_data()
    lowest, highest = get_lowest_highest()
    try:
        sell(lowest)
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Sell order failed:")
        return
    try:
        buy(highest, data[highest]['price'], get_asset_balance('ETH'))
    except (BinanceAPIException, BinanceOrderException) as e:
        print(e)
        logging.exception("Buy order failed:")


def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(run, 'interval', minutes=RUN_INTERVAL)
    scheduler.start()
