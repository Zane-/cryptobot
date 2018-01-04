from exchange_utils import *


class low_high_pair_strat:
    ###   DEFAULTS    ###
    WATCHING = ['ICX/ETH', 'TRX/ETH', 'XLM/ETH', 'ADA/ETH', 'IOTA/ETH', 'XRP/ETH', 'NAV/ETH', 'XVG/ETH']
    SELL_PERCENT = 30 # percent of volume to sell in the run function

    def __init__(self, num, watching=WATCHING, sell_percent=SELL_percent):
        self.num = num
        self.watching = watching
        self.sell_percent = sell_percent

    # Returns a tuple containing (lowest, highest) 24hr percent changes
    # among the cryptos in WATCHING.
    def fetch_lowest_highest(self, data):
        low, high = 0, 0
        for ticker in data:
            change = data[ticker]['change']
            if change > high:
                high, highest = change, ticker
            elif change < low:
                low, lowest = change, ticker
        return (lowest, highest)

    def __call__(self, num=None):
        num = self.num if not num else num
        data = fetch_tickers(watching)
        eth_per = fetch_balance('ETH') / num * 0.98
        for _ in range(num):
            lowest, highest = get_lowest_highest(data)
            data.pop(lowest, None)
            data.pop(highest, None)
            try:
                sell(highest, SELL_VOLUME)
            except ccxt.ExchangeError as e:
                print(e)
                return # do not proceed with buy
            buy(lowest, data[lowest]['bid'], eth_per)




