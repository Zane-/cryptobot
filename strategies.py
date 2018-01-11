from datetime import datetime

from exchange_utils import *



class LowHighPairBot:
    """Bot that takes pairs of high/low 24hr changes and swaps them.

    Args:
        num: The number of high/low pairs to swap.
            num=2 would swap the highest 24hr change with the lowest 24
            hr change, and then the second highest 24hr change with the
            second lowest 24 hour change.
        run_hours: A list of hours the bot should run at.
            If run_hours=[0, 6, 12, 18], the bot would only run
            if the hour at the local time of execution was in that list.
        watching: The currencies to watch for and swap.
        pair: The pair to faciliate swapping.
        sell_percent: The percentage of the high currency to swap into the low.
    """
    def __init__(self, num, run_hours, watching, pair, sell_percent):
        self.num = num
        self.run_hours = run_hours
        self.pair = pair
        self.symbols = [f'{ticker}/{pair}' for ticker in watching]
        self.sell_percent = sell_percent

    def get_lowest_highest(self, data):
        """Returns a tuple containing the highest and lowest 24 hr changes in the data."""
        low, high = 0, 0
        for symbol in data.keys():
            change = data[symbol]['change']
            if change > high:
                high, highest = change, symbol
            if change < low:
                low, lowest = change, symbol
        return (lowest, highest)

    def run(self):
        """Swaps the highest and lowest 24hr change symbols self.num times."""
        data = get_symbols(self.symbols)
        for _ in range(self.num):
            lowest, highest = get_lowest_highest(data)
            symbols.remove(lowest)
            symbols.remove(highest)
            swap(highest, lowest, self.sell_percent, auto_adjust=True)

    def start(self):
        """Runs the bot if the hour of the current system time (UTC on Heroku)
        is in self.run_hours.
        """
        # op 2 line scheduler
        if datetime.now().hour not in self.run_hours:
            return
        self.run()



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
            price = get_symbol(symbol)['ask']
            if self.sell_after:
                sell(symbol, 100, price*self.sell_multiplier, auto_adjust=True)
            return True

    def start(self):
        """Runs self.run() every self.interval seconds. Exits if a new currency is detected."""
        while True:
            if self.run(): # returns True if bought something
                break
            sleep(self.interval)



class PoolProfitBot:
    """Bot that pulls profit out of short term positions and places it into a long one.

    Args:
        interval: The interval to check for profits in seconds.
        feeders: A dictionary mapping currencies to sell profits from with their intial investments and
            profit to sell at.
            Example:
            feeders = {
                'TRX': {
                    'initial': 10,
                    'sell_point': 13 # sell profit whenever USD value goes past $13
                }
            }
            Notes: All feeders must share a common pair with the pool.
                If the profit does not meet the minimum cost requirements
                of the exchange (0.01 ETH / 0.001 BTC on Binance), then an
                InvalidOrder exception will be raised upon attempting to swap
                the feeder profits into the pool.

        pool: The currency to pool profits into.
        pair: The pair to buy/sell currencies with.
    """
    def __init__(self, interval, feeders, pool='XLM', pair='BTC'):
        self.interval = interval
        self.feeders = feeders
        self.pool = f'{pool}/{pair}'
        self.pair = pair

    def check_for_profits(self):
        """Checks if the USD value any of the tickers in feeders is greater
        than the initial value + the profit threshold. If any are, a dictionary
        mapping the ticker to the percentage of the total balance that is profit
        is returned.
        """
        profits = {}
        for ticker in self.feeders.keys():
            usd = get_usd_balance(ticker)
            intial = feeders[ticker][initial]
            sell_point = feeders[ticker][sell_point]

            if usd >= sell_point:
                # proportion of profit to total usd value
                profit_percent = (usd - initial) / usd
                profits[ticker] = profit_percent
        return profits if len(profits.keys()) > 0 else None

    def run(self):
        """Checks for profit and swaps it into the pool."""
        profits = self.check_for_profits()
        if profits is not None:
            for ticker, profit_percent in profits.items():
                symbol = f'{ticker}/{self.pair}'
                swap(symbol, self.pool, profit_percent, auto_adjust=True)

    def start(self):
        """Runs self.run() every self.interval seconds"""
        while True:
            self.run()
            sleep(self.interval)
