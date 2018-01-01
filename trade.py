from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from auth import *

WATCHING = ['ICXETH', 'TRXETH', 'XLMETH', 'ADAETH', 'IOTAETH', 'XRPETH', 'NAVETH', 'XVGETH']


# Returns a dictionary w/ the prices and percent changes of all cryptos in the WATCHING list
def get_watching_data():
    prices = {}
    for ticker in WATCHING:
        data = b.get_ticker(symbol=ticker)
        prices[ticker] = {}
        prices[ticker]['price'] = data['lastPrice']
        prices[ticker]['change'] = data['priceChangePercent']
    return prices

high = lambda x, y: x > y
low = lambda x, y: x < y

def get_greatest_change(comp=high):
    data = get_watching_data()
    greatest = [0, 0]
    for ticker in data:
        change = float(data[ticker]['change'])
        if comp(change, greatest[1]):
            greatest[0] = ticker
            greatest[1] = change
    return greatest


# send eth on gdax to binance, sell into ltc, send to gdax, repeat

# TODO:
# * Add checks to see if withdrawals/deposits have cleared
# * Write the run function
# * Find hosting
