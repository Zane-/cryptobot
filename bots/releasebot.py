import sys
sys.path.append('..')
from exchange_utils import *


class BinanceNewListingBot:
    """Bot that listens for new Binance currency listings and immediately buys.

    Args:
        interval: The time to wait between checks in seconds.
            The Binance API can take 1200 requests per minute as of 1/11/2018,
            though repeated commands may result in a ban.
        pair: The pair to buy with.
        percentage: The percentage of the pair to buy with.
        sell_after: Whether or not to place a limit sell order after.
            Defaults to True.
        sell_multiplier: The price multiplier for the sell order.
            Defaults to 2. (New listings typically jump 100%, though not always)
    """
    def __init__(self, interval, pair, percentage, sell_after=True, sell_multiplier=2):
        self.interval = interval
        self.pair = pair
        self.percentage = percentage
        self.sell_after = sell_after
        self.sell_multiplier = sell_multiplier
        self.start_currencies = self.get_currencies()

    def get_currencies(self):
        """Reloads Binance and returns a set of the currencies."""
        exchange = ccxt.binance({
            'apiKey': keys['binance']['api_key'],
            'secret': keys['binance']['api_secret'],
        })
        exchange.load_markets() # reload the exchange
        return set(exchange.currencies.keys())

    def run(self):
        """Checks if there is a difference between the currencies at the time of the
        bot's intial execution and now. If there is a difference, the bot places
        a buy order for the first currency in the difference, and then places
        a limit sell order if self.sell_after=True for the price of the
        ask * price_multiplier.
        """
        difference = self.get_currencies().difference(self.start_currencies)
        if len(difference) > 0:
            symbol = f'{list(difference)[0]}/{self.pair}'
            buy(symbol, self.percentage, auto_adjust=True)
            print(f'New currency detected: bought {symbol} with {self.percentage} of {self.pair}')
            if self.sell_after:
                price = get_symbol(symbol)['ask'] * self.sell_multiplier
                sell(symbol, 100, price, auto_adjust=True)
            return True

    def start(self):
        """Runs self.run() every self.interval seconds. Exits if a new currency is detected."""
        count = 1
        while True:
            if self.run(): # returns True if bought something
                break
            sleep(self.interval)
            print(f'Attempt #{count}')
            count += 1



def main():
    INTERVAL = 10 # check every 3 seconds
    PAIR = 'ETH' # pair to buy/sell with
    PERCENTAGE = 100 # percentage of pair to buy with
    SELL_AFTER = True # whether or not to place a sell order directly after
    SELL_MULTIPLIER = 2 # number to multiply the price by
    bot = BinanceNewListingBot(INTERVAL, PAIR, PERCENTAGE, SELL_AFTER, SELL_MULTIPLIER)
    bot.start()

if __name__ == '__main__':
    main()
