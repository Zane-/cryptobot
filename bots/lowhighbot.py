import sys
from datetime import datetime
sys.path.append('..')
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
        for symbol in data:
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



def main():
    NUM = 2 # number of high/low pairs to swap
    RUN_HOURS = [0, 6, 12, 18] # UTC hours to run at
    WATCHING = ['ICX', 'TRX', 'XLM', 'ADA', 'POWR', 'XRP', 'NAV', 'XVG']
    PAIR = 'ETH'
    SELL_PERCENT = 50 # percent of ticker to sell off each time
    bot = LowHighPairBot(NUM, RUN_HOURS, WATCHING, PAIR, SELL_PERCENT)
    bot.start()

if __name__ == '__main__':
    main()
