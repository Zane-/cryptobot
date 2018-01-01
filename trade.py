from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from auth import *

WATCHING = ['ICXETH', 'TRXETH', 'XLMETH', 'ADAETH', 'IOTAETH', 'XRPETH', 'NAVETH', 'XVGETH']
SELL_VOLUME = 0.3 # percent of volume to sell

# Returns a dictionary w/ the prices and percent changes of all cryptos in the WATCHING list
def get_watching_data():
    prices = {}
    for ticker in WATCHING:
        data = b.get_ticker(symbol=ticker)
        prices[ticker] = {}
        prices[ticker]['price'] = float(data['lastPrice'])
        prices[ticker]['change'] = float(data['priceChangePercent'])
    return prices


high = lambda x, y: x > y
low = lambda x, y: x < y
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


def sell_highest():
    highest = get_greatest_change()
    b.order_market_sell(
        symbol=highest[0],
        quantity=SELL_VOLUME * b.get_asset_balance(asset=greatest[0][0:-3]) # truncate ETH
    )

def buy_lowest():
    highest = get_greatest_change(comp=low)
    b.order_market_buy(
       symbol=highest[0],
       # buy with 97% ETH balance because we sell highest into ETH first
       # and we don't want rounding errors to not let the order go through
       quantity= b.get_asset_balance(asset='ETH') * 0.97 / highest['price']
   )

# TODO:
# * Write the run function
# * Find hosting
