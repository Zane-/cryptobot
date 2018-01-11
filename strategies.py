from datetime import datetime

from exchange_utils import *



class LowHighPairBot:
    ###   DEFAULTS    ###
    def __init__(self, num, run_hours, watching, pair='ETH', sell_percent):
        self.num = num
        self.run_hours = run_hours # list of UTC hours the bot will run at
        self.pair = pair
        self.symbols = [f'{ticker}/{pair}' for ticker in watching]
        self.sell_percent = sell_percent

    # Returns a tuple containing (lowest, highest) 24hr percent changes
    # among the cryptos in WATCHING.
    def get_lowest_highest(self, symbols):
        symbols = get_symbols(symbols)
        low, high = 0, 0
        for symbol in symbols.keys():
            change = symbols[symbol]['change']
            if change > high:
                high, highest = change, symbol
            elif change < low:
                low, lowest = change, symbol
        return (lowest, highest)

    def run(self):
        symbols = self.symbols
        for _ in range(self.num):
            lowest, highest = get_lowest_highest(symbols)
            symbols.remove(lowest)
            symbols.remove(highest)
            swap(highest, lowest, self.pair, self.sell_percent, auto_adjust=True)

    def start(self):
        # op 2 line scheduler
        if datetime.now().hour not in run_hours:
            return
        self.run()



class BinanceNewListingBot:
    def __init__(self, interval, pair, percentage, sell_after=True, sell_multiplier=2):
        self.interval = interval
        self.pair = pair
        self.percentage = percentage
        self.sell_after = sell_after
        self.sell_multiplier = sell_multiplier
        self.start_currencies = self.get_currencies()

    def get_currencies(self):
        exchange = ccxt.binance({
            'apiKey': keys['binance']['api_key'],
            'secret': keys['binance']['api_secret'],
        })
        exchange.load_markets()
        return set(exchange.currencies.keys())

    def run(self):
        difference = self.get_currencies().difference(self.start_currencies)
        if len(difference) > 0:
            symbol = f'{list(difference)[0]}/{self.pair}'
            buy(symbol, self.percentage, auto_adjust=True)
            print(f'New currency detected: bought {symbol} with {self.percentage} of {self.pair}')
            price = get_symbol(symbol)['ask']
            if sell_after:
                sell(symbol, 100, price*sell_multiplier, auto_adjust=True)
            return True

    def start(self):
        while True:
            if self.run(): # returns True if bought something
                break
            sleep(interval)



class PoolProfitBot:
        def __init__(self, interval, feeders, pool='XLM', pair='BTC', base_amount=10.0, profit_threshold=1.0):
            self.interval = interval
            self.feeders = feeders
            self.pool = pool
            self.base_amount = base_amount
            self.profit_threshold = profit_threshold

        def check_for_profits(self):
            profits = []
            for ticker in feeders:
                usd = get_usd_balance(ticker, self.pair)
                if usd > base_amount + profit_threshold:
                    profits.append(ticker)
            return profits if len(profits) > 0 else None

        def run(self):
            profits = self.check_for_profits()
            if profits is not None:
                for ticker in profits:
                    feeder_symbol = f'{ticker}/{self.pair}'
                    pair_before = get_balance(self.pair)
                    pair_usd = get_symbol(f'{self.pair}/USDT')['bid']

                    feeder_ticker_price = get_symbol(feeder_symbol)['bid']
                    feeder_ticker_amount = self.base_amount / (feeder_ticker_price * pair_usd)
                    feeder_percent = feeder_ticker_amount / get_balance(feeder_ticker) * 100
                    sell(feeder_symbol, feeder_percent, auto_adjust=True) # sell off the profit


                    pair_after = get_balance(self.pair)
                    pair_buy_percent = ((pair_after - pair_before) / pair_after) * 100
                    buy(f'{self.pool}/{self.pair}', pair_buy_percent, auto_adjust=True)

        def start(self):
            while True:
                self.run()
                sleep(interval)
