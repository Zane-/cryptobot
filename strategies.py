from datetime import datetime
from exchange_utils import *


class LowHighPairStrat:
    ###   DEFAULTS    ###
    WATCHING = ['ICX', 'TRX', 'XLM', 'ADA', 'IOTA', 'XRP', 'NAV', 'XVG']
    SELL_PERCENT = 50 # percent of volume to sell in the run function

    def __init__(self, num, run_hours, watching=WATCHING, sell_percent=SELL_percent, pair='ETH'):
        self.num = num
        self.run_hours = run_hours #list of UTC hours the bot will run at
        self.watching = watching
        self.sell_percent = sell_percent
        self.pair = pair

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

    def start(self):
        # op 2 line scheduler
        if datetime.now().hour not in run_hours:
            return

        data = fetch_tickers(watching)
        for _ in range(self.num):
            lowest, highest = fetch_lowest_highest(data)
            data.pop(lowest, None)
            data.pop(highest, None)
            swap(highest, lowest, self.sell_percent, self.pair)
