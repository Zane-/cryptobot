import sys
sys.path.append('..')
from exchange_utils import *


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
        than the the sell point. If any are, a dictionary
        mapping the ticker to the percentage of the total balance thattttnnt is profit
        is returned.
        """
        profits = {}
        for ticker in self.feeders:
            usd = get_usd_balance(ticker)
            intial = self.feeders[ticker][initial]
            sell_point = self.feeders[ticker][sell_point]

            if usd >= sell_point:
                # proportion of profit to total usd value
                profit_percent = ((usd - initial) / usd) * 100
                profits[ticker] = profit_percent
        return profits if len(profits) > 0 else None

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



def main():
    INTERVAL = 60 * 60 # 60 minutes
    FEEDERS = { # short term positions here, with initial investments and sell points
        'TRX': {
            'initial': 100,
            'sell_point': 115
        },
        'ADA': {
            'initial': 100,
            'sell_point': 130
        }
    }
    POOL = 'XLM' # long term position here
    PAIR = 'ETH' # pair to buy/sell things with
    bot = PoolProfitBot(INTERVAL, FEEDERS, POOL, PAIR)
    bot.start()

if __name__ == '__main__':
    main()
