from datetime import datetime
from exchange_utils import *



class LowHighPairBot:
    ###   DEFAULTS    ###
    WATCHING = ['ICX', 'TRX', 'XLM', 'ADA', 'IOTA', 'XRP', 'NAV', 'XVG']
    SELL_PERCENT = 50 # percent of volume to sell in the run function

    def __init__(self, num, run_hours, pair='ETH', watching=WATCHING, sell_percent=SELL_PERCENT):
        self.num = num
        self.run_hours = run_hours #list of UTC hours the bot will run at
        self.pair = pair
        self.watching = watching
        self.sell_percent = sell_percent

    # Returns a tuple containing (lowest, highest) 24hr percent changes
    # among the cryptos in WATCHING.
    def get_lowest_highest(self, tickers):
        tickers = fetch_tickers(tickers)
        low, high = 0, 0
        for ticker in tickers.keys():
            change = tickers[ticker]['change']
            if change > high:
                high, highest = change, ticker
            elif change < low:
                low, lowest = change, ticker
        return (lowest, highest)

    def run(self, num, tickers=None):
        num = self.num if num is None else num
        tickers = self.watching if tickers is None else tickers
        for _ in range(num):
            lowest, highest = get_lowest_highest(tickers)
            data.pop(lowest, None)
            data.pop(highest, None)
            swap(highest, lowest, self.pair, self.sell_percent, auto_adjust=True)

    def start(self, *, num=None, run_hours=None):
        num = self.num if num is None else num
        run_hours = self.run_hours if run_hours is none else run_hours
        # op 2 line scheduler
        if datetime.now().hour not in run_hours:
            return
        self.run(num)



class BinanceNewListingBot:
    def __init__(self, interval, pair, percentage):
        self.interval = interval
        self.pair = pair
        self.percentage = percentage
        self.start_symbols = self.get_symbols()

    def get_symbols(self):
        exchange = ccxt.binance({
            'apiKey': keys['binance']['api_key'],
            'secret': keys['binance']['api_secret'],
        })
        exchange.load_markets()
        return exchange.symbols

    def run(self):
        difference = [s for s in self.get_symbols() if s not in self.start_symbols]
        if len(difference) > 0:
            buy(difference[0][0:-4], self.pair, self.percentage, auto_adjust=True)
            print(f'New currency detected: bought {difference[0][0:-4]} with {self.percentage} of {self.pair}')
            return True

    def start(self, *, interval=None):
        interval = self.interval if interval is None else interval
        while True:
            if self.run(): # returns t
                break
            sleep(interval)



class PoolProfitBot:
        def __init__(self, interval, feeders, pool='XLM',  pair='BTC', base_amount=10.0, profit_threshold=1.0):
            self.interval = interval
            self.feeders = feeders
            self.pool = pool
            self.pair = pair
            self.base_amount = base_amount
            self.profit_threshold = profit_threshold

        def check_for_profits(self, tickers=None):
            tickers = self.feeders if tickers is None else tickers
            profits = []
            for ticker in tickers:
                usd = get_usd_balance(ticker, self.pair)
                if usd > base_amount + profit_threshold:
                    profits.append(ticker)
            return profits if len(profits) > 0 else None

        def run(self, feeders, pool, pair, base_amount, profit_threshold):
            profits = self.check_for_profits()
            pair_usd = get_ticker(pair, 'USDT')['last']
            if profits is not None:
                for ticker in profits:
                    pair_before = get_balance(pair)
                    pair_price = get_ticker(ticker, pair)['last']
                    ticker_usd = get_usd_balance(ticker, pair)
                    amount = pair_usd * pair_price / (ticker_usd - base_amount)
                    percent = amount / get_balance(ticker) * 100
                    sell(ticker, pair, percent, auto_adjust=True) # sell off the profit

                    pair_after = get_balance(self.pair)
                    pair_buy_percent = ((pair_after - pair_before) / pair_after) * 100
                    buy(pool, pair, pair_buy_percent, auto_adjust=True)

        def start(self, *, interval=None, feeders=None, pool=None, pair=None, base_amount=None, profit_threshold=None):
            interval = self.interval if interval is None else interval
            feeders = self.feeders if feeders is None else feeders
            pool = self.pool if pool is None else pool
            pair = self.pair if pair is None else pair
            base_amount = self.base_amount if base_amount is None else base_amount
            profit_threshold = self.profit_threshold if profit_threshold is None else profit_threshold
            while True:
                self.run(feeders, pool, pair, base_amount, profit_threshold)
                sleep(interval)
