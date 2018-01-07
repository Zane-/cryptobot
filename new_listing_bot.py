import json
import ccxt
from math import floor
from time import sleep
from twilio.rest import Client


twilio = Client('ACec9c935277a80dc7aaedab9c77a9b2c4', 'c21e95ec6f157941a424cc415cce1c45')

with open('api_keys.json') as f:
    keys = json.load(f)

exchange = ccxt.binance({
    'apiKey': keys['binance']['api_key'],
    'secret': keys['binance']['api_secret'],
})


# Places a market buy order for the ticker using the specified percentage of the pair
# currency. If the order does not go through, and auto_adjust is True,
#  another is placed for 1% less volume.
def buy(ticker, pair_percent, pair='ETH', auto_adjust=True):
    amount = floor(fetch_balance(pair) * (pair_percent/100) / fetch_ticker(ticker)['last'])
    buy_placed = False
    while not buy_placed:
        try:
            order = exchange.create_market_buy_order(ticker + f'/{pair}', amount)
        except ccxt.InsufficientFunds as e:
            if auto_adjust:
                amount *= 0.99 # step down by 1% until order placed
            sleep(1)
            continue
        except (ccxt.ExchangeError, ccxt.NetworkError) as e:
            if auto_adjust and e.__class__.__name__ == 'ExchangeError':
                amount *= 0.99 # step down by 1% until order placed
            print(e)
            sleep(1)
            continue
        buy_placed = True
    return order


class BinanceNewListingBot:
    def __init__(self, percentage, pair='ETH'):
        self.percentage = percentage
        self.pair = pair
        self.start_symbols = self.fetch_symbols()

    def fetch_symbols(self):
        exchange = ccxt.binance({
            'apiKey': keys['binance']['api_key'],
            'secret': keys['binance']['api_secret'],
        })
        exchange.load_markets()
        return exchange.symbols

    def start(self, refresh_time=10):
        count = 0
        while True:
            print(f'Scanning for shitcoins . . . Attempt #{count}')
            difference = [s for s in self.fetch_symbols() if s not in self.start_symbols]
            if len(difference) > 0:
                twilio.messages.create(
                    to='+15126296980',
                    from_='+14344656948',
                    message=f'BINANCE NEW COIN LISTING: {difference[0][0:-4]}')
                twilio.messages.create(
                    to='+14349879841',
                    from_='+14344656948',
                    message=f'BINANCE NEW COIN LISTING: {difference[0][0:-4]}')
                buy(difference[0][0:-4], self.percentage, self.pair)
                print(f'New currency detected: bought {difference[0][0:-4]} with {self.percentage} of {self.pair}')
                break
            count += 1
            sleep(refresh_time)


if __name__ == '__main__':
    bot = BinanceNewListingBot(100)
    bot.start()
