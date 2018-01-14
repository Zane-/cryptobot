import unittest

from exchange_utils import *
from strategies import *


class ExchangeUtilsTest(unittest.TestCase):

    def test_get_balance(self):
        balance = get_balance('ETH')
        self.assertIsInstance(balance, float)

    def test_get_nonzero_balances(self):
        nonzero_balances = get_nonzero_balances()
        self.assertIsInstance(nonzero_balances, dict)

    def test_get_symbol(self):
        vol_btc = get_symbol('ETH/BTC')['volume']
        self.assertTrue(vol_btc > 0)

    def test_get_symbols(self):
        symbols = get_symbols('XLM/ETH', 'XLM/BTC')
        self.assertEqual(len(symbols.keys()), 2)

    def test_get_all_symbols(self):
        symbols = get_all_symbols()
        self.assertEqual(len(symbols.keys()), len(exchange.symbols))

    def test_sell(self):
        price = get_symbol('BNB/ETH')['ask'] * 1.5
        order = sell('BNB/ETH', 100, price)
        cancel(order)
        self.assertTrue(order['id'] is not None)

    def test_buy(self):
        price = get_symbol('BNB/ETH')['ask'] * 0.6
        order = buy('BNB/ETH', 100, price)
        cancel(order)
        self.assertTrue(order['id'] is not None)

    def test_get_open_orders(self):
        price = get_symbol('BNB/ETH')['ask']
        sell_order = sell('BNB/ETH', 100, price*2)
        self.assertEqual(len(get_open_orders('BNB')['sell']), 1)
        cancel(sell_order)
        buy_order = buy('BNB/ETH', 100, price*0.8)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 1)
        cancel(buy_order)

    def test_cancel(self):
        price = get_symbol('BNB/ETH')['ask']
        buy_order = buy('BNB/ETH', 100, price*0.8)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 1)
        cancel(buy_order)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 0)

    def test_cancel_orders(self):
        price = get_symbol('BNB/ETH')['ask']
        sell_order = sell('BNB/ETH', 100, price*2)
        self.assertEqual(len(get_open_orders('BNB')['sell']), 1)
        cancel_orders('BNB', side='sell')
        self.assertEqual(len(get_open_orders('BNB')['sell']), 0)

        buy_order = buy('BNB/ETH', 100, price*0.8)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 1)
        cancel_orders('BNB', side='buy')
        self.assertEqual(len(get_open_orders('BNB')['buy']), 0)

    def test_cancel_all_orders(self):
        price = get_symbol('BNB/ETH')['ask']
        sell_order = sell('BNB/ETH', 100, price*2)
        self.assertEqual(len(get_open_orders('BNB')['sell']), 1)
        cancel_all_orders()
        self.assertEqual(len(get_open_orders('BNB')['sell']), 0)

        buy_order = buy('BNB/ETH', 100, price*0.8)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 1)
        cancel_all_orders()
        self.assertEqual(len(get_open_orders('BNB')['buy']), 0)

    def test_get_usd_balance(self):
        balance = get_usd_balance('ETH')
        self.assertIsInstance(get_usd_balance('ETH'), float)

    def test_get_portfolio(self):
        portfolio = get_portfolio()
        self.assertIsInstance(portfolio, dict)



class LowHighPairBotTest(unittest.TestCase):

    def test_get_lowest_highest(self):
        data = {
            'XLM': {'change': 15},
            'BTC': {'change': 20},
            'ETH': {'change': 100},
            'TRX': {'change': -50}
        }
        bot = LowHighPairBot(2, [0], ['TRX'], 'ETH', 50)
        lowest, highest = bot.get_lowest_highest(data)
        self.assertEqual(lowest, 'TRX')
        self.assertEqual(highest, 'ETH')


if __name__ == '__main__':
    unittest.main()
